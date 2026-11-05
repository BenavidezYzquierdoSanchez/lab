#!/usr/bin/env python3
"""Actualiza las ocho vistas agregadas de FraudCloud ejecutando SQL REAL en Amazon Athena.

No necesita access keys; usa IAM Role de EC2, o --profile para entorno local.
En caso de fallo, no reemplaza las exportaciones anteriores.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import boto3
from botocore.exceptions import BotoCoreError, ClientError

ROOT = Path(__file__).resolve().parents[1]


def obtener_s3(response: dict) -> tuple[str, str]:
    result_config = response['QueryExecution'].get('ResultConfiguration', {})
    uri = result_config.get('OutputLocation')
    if not uri:
        raise RuntimeError('La consulta no devolvió OutputLocation S3; revise ajustes del workgroup.')
    parsed = urlsplit(uri)
    if parsed.scheme != 's3' or not parsed.netloc or not parsed.path.strip('/'):
        raise RuntimeError(f'OutputLocation no es una URI S3 válida: {uri!r}')
    return parsed.netloc, parsed.path.lstrip('/')


def wait_athena(client, execution_id: str, timeout_s: int) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        r = client.get_query_execution(QueryExecutionId=execution_id)
        state = r['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            return r
        if state in ('FAILED', 'CANCELLED'):
            cause = r['QueryExecution']['Status'].get('StateChangeReason', '')
            raise RuntimeError(f'Athena {state} para {execution_id}: {cause}')
        time.sleep(3)
    raise TimeoutError(f'Tiempo de espera agotado para consulta Athena {execution_id}')


def sincronizar(args) -> None:
    session_kwargs = {'region_name': args.region}
    if args.profile:
        session_kwargs['profile_name'] = args.profile
    session = boto3.Session(**session_kwargs)
    athena = session.client('athena')
    s3 = session.client('s3')
    sql_paths = sorted((ROOT / 'sql').glob('*.sql'))
    if len(sql_paths) != 8:
        raise RuntimeError(f'Se esperaban 8 archivos SQL, se hallaron {len(sql_paths)}.')
    target = Path(args.output_dir).resolve() if args.output_dir else ROOT / 'data' / 'athena_results'
    target.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix='.athena_staging_',dir=target.parent))
    query_ids = {}
    try:
        for i, path in enumerate(sql_paths, start=1):
            sql = path.read_text(encoding='utf-8')
            sql = sql.replace('{{DATABASE}}', f'"{args.database}"').replace('{{TABLE}}', f'"{args.table}"')
            print(f'[{i}/8] Ejecutando {path.name} ...',flush=True)
            query = athena.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': args.database, 'Catalog': 'AwsDataCatalog'},
                ResultConfiguration={'OutputLocation': f's3://{args.bucket}/athena-results/'},
                WorkGroup=args.workgroup,
            )
            qid=query['QueryExecutionId']
            execution=wait_athena(athena,qid,args.timeout)
            bucket,key=obtener_s3(execution)
            s3.download_file(bucket, key, str(staged / (path.stem + '.csv')))
            query_ids[path.stem]=qid
            print(f'   OK: {path.stem}.csv',flush=True)
        meta={
            'synced_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'region':args.region,'database':args.database,'table':args.table,
            'workgroup':args.workgroup, 'queries':query_ids,
        }
        (staged/'_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
        # publicar solo al completar el lote. Copias individuales atomicas.
        for src in staged.glob('*.csv'):
            src.replace(target/src.name)
        (staged/'_metadata.json').replace(target/'_metadata.json')
        print(f'Listo: {len(query_ids)} exportaciones reales de Athena en {target}',flush=True)
    finally:
        shutil.rmtree(staged,ignore_errors=True)


def main():
    p=argparse.ArgumentParser(description='Sincronizar agregados Athena con dashboard EC2')
    p.add_argument('--region',default='us-east-1')
    p.add_argument('--bucket',default='fraude-tarjetas-239635360641-us-east-1')
    p.add_argument('--database',default='fraude_tarjetas_db')
    p.add_argument('--table',default='fraud_transactions')
    p.add_argument('--workgroup',default='fraude-tarjetas-wg')
    p.add_argument('--profile',default=None, help='Solo PC local con IAM Identity Center, nunca guardar claves')
    p.add_argument('--output-dir',default=None)
    p.add_argument('--timeout',type=int,default=240)
    args=p.parse_args()
    try:
        sincronizar(args)
    except (RuntimeError, TimeoutError, ClientError, BotoCoreError) as e:
        p.exit(1,f'ERROR: {e}\n')


if __name__=='__main__':
    main()
