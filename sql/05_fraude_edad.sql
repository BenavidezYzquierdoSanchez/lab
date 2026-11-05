-- ¿Cuál es la tasa de fraude por grupo etario? No expone edad exacta.
SELECT edad_grupo, COUNT(*) AS transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS fraudes,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct
FROM {{DATABASE}}.{{TABLE}}
GROUP BY edad_grupo ORDER BY CASE edad_grupo
  WHEN '18-25' THEN 1 WHEN '26-35' THEN 2 WHEN '36-50' THEN 3
  WHEN '51-65' THEN 4 ELSE 5 END;
