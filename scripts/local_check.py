"""Comprueba el CSV del usuario y genera resultados LOCALES equivalentes a las 8 SQL.

NO realiza consultas AWS: los CSV bajo data/local_results/sql_preview/ son
agregaciones Python, NO evidencias de Athena. No modifica la fuente original.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

REQ = [
    'es_fraude', 'monto_winsorizado_99', 'monto_percentil_categoria',
    'monto_vs_categoria', 'edad_grupo', 'distancia_cliente_comercio_km',
    'es_noche', 'es_fin_de_semana', 'es_fin_de_semana_noche',
    'es_noche_high_risk', 'high_risk_cat', 'mes', 'dia'
]
FLAGS = ['es_fraude', 'es_noche', 'es_fin_de_semana',
         'es_fin_de_semana_noche', 'es_noche_high_risk', 'high_risk_cat']
AGE_GROUPS = ['18-25','26-35','36-50','51-65','65+']

p = argparse.ArgumentParser(description='Auditoría local CSV real + previa de 8 SQL')
p.add_argument('--csv', required=True)
p.add_argument('--outdir', default='data/local_results')
a = p.parse_args()
out = Path(a.outdir)
out.mkdir(parents=True, exist_ok=True)
previews = out / 'sql_preview'
previews.mkdir(parents=True, exist_ok=True)


def group_row(counter, fraud, amount):
    counter[0] += 1
    counter[1] += fraud
    counter[2] += amount if fraud else 0.0


def pct(fraud, size):
    return round(100 * fraud / size, 4) if size else 0.0


def export(filename, keycol, groups, order=None, with_amount=False):
    keys = order if order is not None else sorted(groups)
    head = [keycol, 'transacciones', 'fraudes', 'tasa_fraude_pct']
    if with_amount:
        head += ['suma_monto_winsorizado_fraude']
    with (previews / filename).open('w', encoding='utf-8', newline='') as fp:
        w = csv.writer(fp)
        w.writerow(head)
        for k in keys:
            if k not in groups:
                continue
            t, f, am = groups[k]
            row = [k, t, f, pct(f, t)]
            if with_amount:
                row.append(round(am, 2))
            w.writerow(row)


nulls = Counter()
invalid_types = Counter()
numeric_min = {}
numeric_max = {}
groups = defaultdict(lambda: defaultdict(lambda: [0, 0, 0.0]))
source_rows = valid_rows = invalid_rows = 0
fraud_rows = 0
sum_amount = 0.0
fraud_amount = 0.0

with Path(a.csv).open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames or []
    missing = set(REQ) - set(columns)
    if missing:
        raise SystemExit('Columnas faltantes del CSV real: ' + ', '.join(sorted(missing)))
    for r in reader:
        source_rows += 1
        for c in columns:
            if r.get(c) is None or not str(r[c]).strip():
                nulls[c] += 1
        try:
            vals = {c: float(r[c]) for c in REQ if c != 'edad_grupo'}
            if any(not math.isfinite(v) for v in vals.values()):
                raise ValueError('infinito/NaN')
            if any(vals[c] not in (0.0, 1.0) for c in FLAGS):
                raise ValueError('etiqueta binaria no válida')
            if vals['monto_winsorizado_99'] < 0 or not 0 <= vals['monto_percentil_categoria'] <= 1:
                raise ValueError('monto/percentil fuera de rango')
            if vals['monto_vs_categoria'] < 0 or vals['distancia_cliente_comercio_km'] < 0:
                raise ValueError('relacion/distancia negativa')
            if vals['mes'] not in range(1,13) or vals['dia'] not in range(1,32):
                raise ValueError('mes/dia incorrectos')
            if r['edad_grupo'] not in AGE_GROUPS:
                raise ValueError('grupo de edad inesperado')
            fval = int(vals['es_fraude'])
            month = int(vals['mes'])
            amount = vals['monto_winsorizado_99']
            distance = vals['distancia_cliente_comercio_km']
        except (TypeError, ValueError) as exc:
            invalid_rows += 1
            invalid_types[str(exc)] += 1
            continue
        valid_rows += 1
        fraud_rows += fval
        sum_amount += amount
        fraud_amount += amount if fval else 0
        for col, x in vals.items():
            numeric_min[col] = min(numeric_min.get(col, x), x)
            numeric_max[col] = max(numeric_max.get(col, x), x)
        if amount < 25: rng='00 - menor a 25'
        elif amount < 100: rng='01 - 25 a 99.99'
        elif amount < 300: rng='02 - 100 a 299.99'
        else: rng='03 - 300 o mas'
        if distance < 20: drng='00 - menos de 20 km'
        elif distance < 60: drng='01 - 20 a 59.99 km'
        elif distance < 100: drng='02 - 60 a 99.99 km'
        else: drng='03 - 100 km o mas'
        for dim, key in [
            ('02_fraude_por_monto', rng), ('03_fraude_noche', int(vals['es_noche'])),
            ('04_fraude_categoria_riesgo', int(vals['high_risk_cat'])),
            ('05_fraude_edad', r['edad_grupo']), ('06_fraude_mes', month),
            ('07_fraude_fin_semana', int(vals['es_fin_de_semana'])),
            ('08_fraude_por_distancia', drng),
        ]:
            group_row(groups[dim][key], fval, amount)

summary = {
    'archivo': Path(a.csv).name,
    'procedencia': 'ARCHIVO PROCESADO APORTADO POR EL USUARIO; NO VERIFICADO CONTRA KAGGLE',
    'filas_raw': source_rows, 'validas': valid_rows, 'invalidas': invalid_rows,
    'fraudes': fraud_rows, 'legitimas': valid_rows-fraud_rows,
    'tasa_fraude_pct': pct(fraud_rows, valid_rows),
    'suma_monto_winsorizado': round(sum_amount, 2),
    'suma_monto_winsorizado_fraude': round(fraud_amount, 2),
    'advertencia_monto': 'Monto winsorizado al percentil 99, NO importe original ni moneda conocida',
    'columnas_total': len(columns), 'columnas': columns,
    'campos_nulos': dict(nulls), 'errores_validacion': dict(invalid_types),
    'rangos_numericos': {c:{'min':numeric_min[c], 'max':numeric_max[c]} for c in numeric_min},
}
(out / 'resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
(out / 'diccionario_columnas.json').write_text(json.dumps(columns, ensure_ascii=False, indent=2), encoding='utf-8')
with (out/'kpis.csv').open('w', encoding='utf-8', newline='') as fp:
    w=csv.writer(fp)
    w.writerow(['indicador', 'valor'])
    for key in ['filas_raw','validas','invalidas','fraudes','legitimas','tasa_fraude_pct','suma_monto_winsorizado','suma_monto_winsorizado_fraude']:
        w.writerow([key,summary[key]])
with (previews / '01_kpis_fraude.csv').open('w', encoding='utf-8', newline='') as fp:
    w = csv.writer(fp)
    w.writerow(['total_transacciones','transacciones_fraude','transacciones_legitimas',
                'tasa_fraude_pct','suma_monto_winsorizado','suma_monto_winsorizado_fraude'])
    w.writerow([valid_rows, fraud_rows, valid_rows-fraud_rows, pct(fraud_rows, valid_rows),
                round(sum_amount,2),round(fraud_amount,2)])
for n, key, order, amt in [
    ('02_fraude_por_monto','rango_monto',None,True),
    ('03_fraude_noche','es_noche',[0,1],False),
    ('04_fraude_categoria_riesgo','high_risk_cat',[0,1],False),
    ('05_fraude_edad','edad_grupo',AGE_GROUPS,False),
    ('06_fraude_mes','mes',list(range(1,13)),False),
    ('07_fraude_fin_semana','es_fin_de_semana',[0,1],False),
    ('08_fraude_por_distancia','rango_distancia',None,False),
]:
    export(n+'.csv',key,groups[n],order,amt)
with Path(a.csv).open('rb') as fp:
    sha = hashlib.file_digest(fp, 'sha256').hexdigest()
summary['sha256'] = sha
(out / 'resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ('filas_raw','validas','invalidas','fraudes',
      'tasa_fraude_pct','sha256')}, ensure_ascii=False, indent=2))
print('Vistas locales creadas en:',previews)
