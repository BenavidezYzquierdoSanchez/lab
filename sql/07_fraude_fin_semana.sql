-- Fin de semana sí/no, de acuerdo con variable derivada entregada.
SELECT es_fin_de_semana, COUNT(*) AS transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS fraudes,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct
FROM {{DATABASE}}.{{TABLE}}
GROUP BY es_fin_de_semana ORDER BY es_fin_de_semana;
