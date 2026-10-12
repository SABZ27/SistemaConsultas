-- Verificación de esquema MySQL (local). 
-- Requiere DB_NAME o ejecutar en base correcta.

SELECT COUNT(*) AS tablas_total
FROM information_schema.tables
WHERE table_schema = (SELECT DATABASE())
  AND table_type = 'BASE TABLE';

-- Verificar cada tabla tiene PK, estado, creado, actualizado y al menos un índice único
SELECT t.table_name,
       (SELECT COUNT(*) FROM information_schema.table_constraints tc
        WHERE tc.table_schema = t.table_schema
          AND tc.table_name = t.table_name
          AND tc.constraint_type = 'PRIMARY KEY') AS tiene_pk,
       SUM(CASE WHEN c.column_name = 'estado' THEN 1 ELSE 0 END) AS tiene_estado,
       SUM(CASE WHEN c.column_name = 'creado' THEN 1 ELSE 0 END) AS tiene_creado,
       SUM(CASE WHEN c.column_name = 'actualizado' THEN 1 ELSE 0 END) AS tiene_actualizado,
       (SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics s
        WHERE s.table_schema = t.table_schema
          AND s.table_name = t.table_name
          AND s.non_unique = 0) AS indices_unicos
FROM information_schema.tables t
LEFT JOIN information_schema.columns c
  ON c.table_schema = t.table_schema AND c.table_name = t.table_name
WHERE t.table_schema = (SELECT DATABASE())
  AND t.table_type = 'BASE TABLE'
GROUP BY t.table_name, t.table_schema
ORDER BY t.table_name;
