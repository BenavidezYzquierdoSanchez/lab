-- Análisis por rango de MONTO WINSORIZADO, no por importe original.
WITH t AS (
 SELECT CASE WHEN monto_winsorizado_99 < 25 THEN '00 - menor a 25'
             WHEN monto_winsorizado_99 < 100 THEN '01 - 25 a 99.99'
             WHEN monto_winsorizado_99 < 300 THEN '02 - 100 a 299.99'
             ELSE '03 - 300 o mas' END AS rango_monto,
        es_fraude, monto_winsorizado_99
 FROM {{DATABASE}}.{{TABLE}}
)
SELECT rango_monto, COUNT(*) AS transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS fraudes,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct,
       ROUND(SUM(CASE WHEN es_fraude=1 THEN monto_winsorizado_99 ELSE 0 END), 2) AS suma_monto_winsorizado_fraude
FROM t GROUP BY rango_monto ORDER BY rango_monto;
