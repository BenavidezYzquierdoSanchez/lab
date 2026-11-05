-- high_risk_cat es una BANDERA binaria; NO representa una categoría textual.
SELECT high_risk_cat, COUNT(*) AS transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS fraudes,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct
FROM {{DATABASE}}.{{TABLE}}
GROUP BY high_risk_cat ORDER BY high_risk_cat;
