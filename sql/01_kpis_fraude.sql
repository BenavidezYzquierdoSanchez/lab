-- KPI generales del CSV procesado: monto winsorizado NO es importe original.
SELECT COUNT(*) AS total_transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS transacciones_fraude,
       SUM(CASE WHEN es_fraude = 0 THEN 1 ELSE 0 END) AS transacciones_legitimas,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct,
       ROUND(SUM(monto_winsorizado_99), 2) AS suma_monto_winsorizado,
       ROUND(SUM(CASE WHEN es_fraude = 1 THEN monto_winsorizado_99 ELSE 0 END), 2) AS suma_monto_winsorizado_fraude
FROM {{DATABASE}}.{{TABLE}};
