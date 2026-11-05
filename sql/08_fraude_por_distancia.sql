-- Distancia calculada en km; franjas heurísticas descriptivas.
WITH t AS (
 SELECT CASE WHEN distancia_cliente_comercio_km < 20 THEN '00 - menos de 20 km'
             WHEN distancia_cliente_comercio_km < 60 THEN '01 - 20 a 59.99 km'
             WHEN distancia_cliente_comercio_km < 100 THEN '02 - 60 a 99.99 km'
             ELSE '03 - 100 km o mas' END AS rango_distancia, es_fraude
 FROM {{DATABASE}}.{{TABLE}}
)
SELECT rango_distancia, COUNT(*) AS transacciones,
       SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) AS fraudes,
       ROUND(100.0 * SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS tasa_fraude_pct
FROM t GROUP BY rango_distancia ORDER BY rango_distancia;
