-- Comparar la tasa de fraude cuando es_noche es 0 versus 1.
SELECT es_noche, COUNT(*) AS transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS fraudes,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct
FROM {{DATABASE}}.{{TABLE}}
GROUP BY es_noche ORDER BY es_noche;
