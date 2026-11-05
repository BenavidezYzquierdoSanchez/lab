"""AWS Glue 5.0 / Spark ETL para CSV procesado REAL recibido del usuario.

NO se afirma que monto_winsorizado_99 represente el importe contable original.
Las columnas identificatorias/quasi-identificatorias detalladas no se propagan a curated.
"""
import sys
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, functions as F

args = getResolvedOptions(sys.argv, ['RAW_PATH', 'CURATED_PATH'])
spark = SparkSession.builder.getOrCreate()
spark.conf.set('spark.sql.session.timeZone', 'UTC')
raw = (spark.read.option('header', True).option('inferSchema', False)
       .option('mode', 'FAILFAST').csv(args['RAW_PATH']))
required = {
    'es_fraude', 'monto_winsorizado_99', 'monto_percentil_categoria',
    'monto_vs_categoria', 'edad_grupo', 'distancia_cliente_comercio_km',
    'es_noche', 'es_fin_de_semana', 'es_fin_de_semana_noche',
    'es_noche_high_risk', 'high_risk_cat', 'mes', 'dia'
}
missing = sorted(required - set(raw.columns))
if missing:
    raise ValueError(f'Columnas no encontradas en el CSV real: {missing}')

num_double = ['monto_winsorizado_99', 'monto_percentil_categoria',
              'monto_vs_categoria', 'distancia_cliente_comercio_km']
num_int = ['es_fraude', 'es_noche', 'es_fin_de_semana', 'es_fin_de_semana_noche',
           'es_noche_high_risk', 'high_risk_cat', 'mes', 'dia']

# Cast explícito; no usar inferSchema para evitar tipos distintos en cada carga.
working = raw.select(
    *(F.trim(F.col(c)).cast('double').alias(c) for c in num_double),
    *(F.trim(F.col(c)).cast('int').alias(c) for c in num_int),
    F.trim(F.col('edad_grupo')).alias('edad_grupo')
)

valid_expr = F.lit(True)
for c in num_double:
    valid_expr = valid_expr & F.col(c).isNotNull() & (~F.isnan(c))
for c in num_int:
    valid_expr = valid_expr & F.col(c).isNotNull()
for c in ['es_fraude', 'es_noche', 'es_fin_de_semana',
          'es_fin_de_semana_noche', 'es_noche_high_risk', 'high_risk_cat']:
    valid_expr = valid_expr & F.col(c).isin(0, 1)
valid_expr = (valid_expr & (F.col('monto_winsorizado_99') >= 0)
              & F.col('monto_percentil_categoria').between(0, 1)
              & (F.col('monto_vs_categoria') >= 0)
              & (F.col('distancia_cliente_comercio_km') >= 0)
              & F.col('mes').between(1, 12)
              & F.col('dia').between(1, 31)
              & F.col('edad_grupo').isin('18-25', '26-35', '36-50', '51-65', '65+'))
source_rows = working.count()
valid = working.filter(valid_expr)
valid_rows = valid.count()
if valid_rows == 0:
    raise ValueError('No hay filas válidas para Parquet; se evita sobrescribir curated')
if valid_rows < source_rows:
    print(f'ATENCION: filas rechazadas por regla de calidad: {source_rows-valid_rows}')

# Únicamente campos analíticos permitidos, sin edad exacta, población ciudad,
# hora codificada ni posibles identificadores. No se elimina duplicados porque
# no existe ID de operación que permita determinar repetición real.
curated = valid.withColumn('ingest_date', F.current_date().cast('string'))
(curated.coalesce(2).write.mode('overwrite').option('compression', 'snappy')
 .partitionBy('ingest_date').parquet(args['CURATED_PATH']))
print(f'ETL_OK raw_rows={source_rows} valid_rows={valid_rows} '
      f'rejected={source_rows-valid_rows} curated={args["CURATED_PATH"]}')
