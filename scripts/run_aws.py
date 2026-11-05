"""Orquestador: desplegar, subir datos y ETL, catalogar, ejecutar SQL y exportar métricas.
Requiere AWS credentials configuradas, boto3, y pagos habilitados. No se ejecuta solo.
"""
import argparse, json, pathlib, re, subprocess, sys, time
import boto3
from botocore.exceptions import ClientError
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description='AWS Fraud pipeline 2026')
p.add_argument('step',choices=['deploy','upload','etl','catalog','queries','all','status','destroy'])
p.add_argument('--region',default='us-east-1')
p.add_argument('--stack',default='fraude-tarjetas-lab')
p.add_argument('--project',default='fraude-tarjetas')
p.add_argument('--email',help='Necesario para deploy: alerta de presupuesto')
p.add_argument('--budget',type=float,default=5)
p.add_argument('--data',help='CSV real: data/real/fraude_tarjeta_credito_process.csv')
p.add_argument('--confirm-destroy',action='store_true',help='Elimina objetos y stack: irreversible')
a=p.parse_args()
session=boto3.Session(region_name=a.region)
cf=session.client('cloudformation'); s3=session.client('s3'); glue=session.client('glue'); athena=session.client('athena')

def outputs():
    r=cf.describe_stacks(StackName=a.stack)['Stacks'][0]
    return {i['OutputKey']:i['OutputValue'] for i in r['Outputs']}
def deploy():
    if not a.email or '@' not in a.email:raise SystemExit('Ingrese --email usuario@dominio para AWS Budgets')
    cmd=['aws','cloudformation','deploy','--template-file',str(ROOT/'infra/main.yaml'),
         '--stack-name',a.stack,'--capabilities','CAPABILITY_NAMED_IAM','--region',a.region,
         '--parameter-overrides',f'ProjectName={a.project}',f'AlertEmail={a.email}',f'MonthlyBudgetUSD={a.budget}', '--no-fail-on-empty-changeset']
    subprocess.run(cmd,check=True)
    print('Stack desplegado:',json.dumps(outputs(),indent=2))
def upload():
    o=outputs(); bucket=o['BucketName']
    script=ROOT/'glue/glue_etl.py'
    s3.upload_file(str(script),bucket,'scripts/glue_etl.py',ExtraArgs={'ServerSideEncryption':'AES256'})
    if not a.data:raise SystemExit('Falta --data: data/real/fraude_tarjeta_credito_process.csv')
    source=pathlib.Path(a.data)
    if not source.exists() or source.suffix.lower()!='.csv':raise SystemExit('No existe CSV: '+str(source))
    # Dejar una sola fuente en raw para evitar un merge de esquemas incompatibles
    objects=s3.list_objects_v2(Bucket=bucket,Prefix='raw/transactions/',MaxKeys=1).get('Contents',[])
    if objects:raise SystemExit('raw/transactions/ ya tiene datos; borre explícitamente los antiguos antes de cargar otro dataset.')
    s3.upload_file(str(source),bucket,'raw/transactions/fraude_tarjeta_credito_process.csv',ExtraArgs={'ServerSideEncryption':'AES256'})
    print('Subido',source,'a',f's3://{bucket}/raw/transactions/fraude_tarjeta_credito_process.csv')
def wait_job(job,run_id):
    while True:
        run=glue.get_job_run(JobName=job,RunId=run_id)['JobRun'];state=run['JobRunState'];print('Glue:',state)
        if state in ('SUCCEEDED','FAILED','TIMEOUT','STOPPED','ERROR','EXPIRED'):
            if state!='SUCCEEDED':raise RuntimeError(f'Glue ETL no terminó: {state}: {run.get("ErrorMessage", "")}')
            return
        time.sleep(15)
def run_etl():
    o=outputs();job=o['GlueJobName'];r=glue.start_job_run(JobName=job);wait_job(job,r['JobRunId'])
def catalog():
    o=outputs();cr=o['CrawlerName'];glue.start_crawler(Name=cr)
    while True:
        time.sleep(12)
        c=glue.get_crawler(Name=cr)['Crawler']; state=c['State'];print('Crawler:',state)
        if state=='READY':
            last=c.get('LastCrawl',{});status=last.get('Status','UNKNOWN')
            if status != 'SUCCEEDED':raise RuntimeError('Crawler: '+status+' '+last.get('ErrorMessage',''))
            break

def get_table(o):
    tables=glue.get_tables(DatabaseName=o['DatabaseName'])['TableList']
    matches=[t['Name'] for t in tables if {'es_fraude','monto_winsorizado_99'} <= {c['Name'] for c in t['StorageDescriptor'].get('Columns',[])}]
    if len(matches)!=1:raise RuntimeError('Debe haber exactamente una tabla curated; encontradas: '+str(matches))
    return matches[0]
def run_queries():
    o=outputs();tbl=get_table(o);wg=o['AthenaWorkGroup'];db=o['DatabaseName']
    output_dir=ROOT/'data'/'athena_results';output_dir.mkdir(exist_ok=True)
    for src in sorted((ROOT/'sql').glob('*.sql')):
        query=src.read_text(encoding='utf-8').replace('{{DATABASE}}',f'"{db}"').replace('{{TABLE}}',f'"{tbl}"')
        r=athena.start_query_execution(QueryString=query,QueryExecutionContext={'Database':db},WorkGroup=wg)
        qid=r['QueryExecutionId']
        while True:
            res=athena.get_query_execution(QueryExecutionId=qid)['QueryExecution'];state=res['Status']['State']
            if state in ('SUCCEEDED','FAILED','CANCELLED'):break
            time.sleep(3)
        if state!='SUCCEEDED':raise RuntimeError(f'{src.name}: Athena {state}: {res["Status"].get("StateChangeReason","")}')
        result=athena.get_query_results(QueryExecutionId=qid)
        dest=output_dir/(src.stem+'.csv');s3_output=res['ResultConfiguration']['OutputLocation']
        match=re.match(r's3://([^/]+)/(.+)',s3_output)
        s3.download_file(match.group(1),match.group(2),str(dest))
        print('SQL OK:',src.name,'->',dest)
def status():
    print(json.dumps(outputs(),indent=2,ensure_ascii=False))
def destroy():
    if not a.confirm_destroy:raise SystemExit('Se requiere --confirm-destroy: ¡destruye todos los datos del bucket!')
    bucket=outputs()['BucketName']
    resource=session.resource('s3').Bucket(bucket)
    resource.objects.all().delete()
    cf.delete_stack(StackName=a.stack)
    cf.get_waiter('stack_delete_complete').wait(StackName=a.stack)
    print('Stack eliminado. Revise CloudWatch, Cost Explorer y otros recursos ajenos al stack.')

if a.step in ('deploy','all'):deploy()
if a.step in ('upload','all'):upload()
if a.step in ('etl','all'):run_etl()
if a.step in ('catalog','all'):catalog()
if a.step in ('queries','all'):run_queries()
if a.step=='status':status()
if a.step=='destroy':destroy()
