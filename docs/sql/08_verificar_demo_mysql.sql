-- ============================================================================
-- 08_verificar_demo_mysql.sql — verificación de la demo (MySQL 8 / Aiven)
-- ============================================================================
-- Fase 6. Ejecutar DESPUES de 03, 04 y 06.
-- SOLO SELECT: no crea objetos, no inserta, no actualiza, no borra, no abre
-- transacciones. Se puede ejecutar las veces que quiera.
--
-- Comprueba tres cosas:
--   1. conteo de las 4 tablas y columna "cumple" contra el minimo
--      (20 para las 3 tablas principales, 10 para servicios_externos).
--   2. FK huérfanos: las 5 claves foráneas de 03, todas deben dar 0.
--   3. coherencia [DEMO]: las bitácoras llevan exito = 0 y los correos
--      estado_envio = FALLIDO, ambos marcados con el prefijo [DEMO].
--      Son datos de demostración, nunca llamadas ni envíos reales.
--
-- Salida esperada: todos los "cumple" = CUMPLE y los huérfanos = 0.
-- ============================================================================


-- 1) Conteo de las 4 tablas --------------------------------------------------
WITH conteos(tabla, categoria, minimo, filas) AS (
    SELECT 'festivos', 'principal', 20, COUNT(*) FROM festivos
    UNION ALL SELECT 'consultas_servicio_externo', 'principal', 20, COUNT(*) FROM consultas_servicio_externo
    UNION ALL SELECT 'correos_enviados', 'principal', 20, COUNT(*) FROM correos_enviados
    UNION ALL SELECT 'servicios_externos', 'secundaria', 10, COUNT(*) FROM servicios_externos
)
SELECT tabla,
       categoria,
       minimo,
       filas,
       CASE WHEN filas >= minimo THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM conteos
ORDER BY categoria, tabla;


-- 2) FK huérfanos (5 claves foráneas de 03), todas deben dar 0 --------------
WITH huerfanos(fk, filas_huerfanas) AS (
    SELECT 'consultas_servicio_externo.servicio_id', COUNT(*) FROM consultas_servicio_externo c LEFT JOIN servicios_externos p ON p.id = c.servicio_id WHERE c.servicio_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'festivos.servicio_id', COUNT(*) FROM festivos c LEFT JOIN servicios_externos p ON p.id = c.servicio_id WHERE c.servicio_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'festivos.consulta_servicio_id', COUNT(*) FROM festivos c LEFT JOIN consultas_servicio_externo p ON p.id = c.consulta_servicio_id WHERE c.consulta_servicio_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'correos_enviados.servicio_id', COUNT(*) FROM correos_enviados c LEFT JOIN servicios_externos p ON p.id = c.servicio_id WHERE c.servicio_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'correos_enviados.consulta_servicio_id', COUNT(*) FROM correos_enviados c LEFT JOIN consultas_servicio_externo p ON p.id = c.consulta_servicio_id WHERE c.consulta_servicio_id IS NOT NULL AND p.id IS NULL
)
SELECT fk,
       filas_huerfanas,
       CASE WHEN filas_huerfanas = 0 THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM huerfanos
ORDER BY fk;


-- 3) Coherencia [DEMO] de las filas sintéticas ------------------------------
SELECT bitacoras_demo,
       correos_demo,
       CASE WHEN bitacoras_demo >= 20 AND correos_demo >= 20
            THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM (
    SELECT
        (SELECT COUNT(*) FROM consultas_servicio_externo
          WHERE exito = 0 AND detalle LIKE '[DEMO]%') AS bitacoras_demo,
        (SELECT COUNT(*) FROM correos_enviados
          WHERE estado_envio = 'FALLIDO' AND respuesta_proveedor LIKE '[DEMO]%') AS correos_demo
) AS marcadas;
