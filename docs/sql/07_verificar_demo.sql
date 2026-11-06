-- ============================================================================
-- 07_verificar_demo.sql — verificación de los datos de demostración (PostgreSQL)
-- ============================================================================
-- Fase 6. Ejecutar DESPUES de 01, 02 y 05 sobre Neon (PostgreSQL 15+).
-- SOLO SELECT: no crea objetos, no inserta, no actualiza, no borra, no abre
-- transacciones ni cambia secuencias. Se puede ejecutar las veces que quiera.
--
-- Comprueba cuatro cosas:
--   1. conteo de las 19 tablas y columna "cumple" contra el minimo
--      (20 para las 12 tablas principales, 10 para las 7 secundarias).
--   2. FK huérfanas: las 24 claves foráneas de 01, todas deben dar 0.
--   3. calificaciones SOLO sobre consultas RESUELTAS.
--   4. ninguna solicitud agendada en domingo.
--
-- Salida esperada: todos los "cumple" = CUMPLE y todos los contadores de
-- huérfanas / incumplimientos = 0.
--
-- Nota de portabilidad: la comprobación de domingo usa EXTRACT(DOW FROM ...),
-- exclusiva de PostgreSQL. En SQLite la expresión equivalente es
-- strftime('%w', fecha_consulta) = '0'. El resto del archivo (conteos,
-- huérfanas y calificaciones) es SQL estándar ejecutable también en SQLite.
-- ============================================================================


-- 1) Conteo por cada una de las 19 tablas -----------------------------------
WITH conteos(tabla, categoria, minimo, filas) AS (
    SELECT 'usuarios', 'principal', 20, COUNT(*) FROM usuarios
    UNION ALL SELECT 'programas_academicos', 'principal', 20, COUNT(*) FROM programas_academicos
    UNION ALL SELECT 'modulos', 'principal', 20, COUNT(*) FROM modulos
    UNION ALL SELECT 'sedes', 'principal', 20, COUNT(*) FROM sedes
    UNION ALL SELECT 'zonas', 'principal', 20, COUNT(*) FROM zonas
    UNION ALL SELECT 'recursos_fisicos', 'principal', 20, COUNT(*) FROM recursos_fisicos
    UNION ALL SELECT 'docentes_modulos', 'principal', 20, COUNT(*) FROM docentes_modulos
    UNION ALL SELECT 'disponibilidad_docente', 'principal', 20, COUNT(*) FROM disponibilidad_docente
    UNION ALL SELECT 'solicitudes_consultas', 'principal', 20, COUNT(*) FROM solicitudes_consultas
    UNION ALL SELECT 'comentarios', 'principal', 20, COUNT(*) FROM comentarios
    UNION ALL SELECT 'notificaciones', 'principal', 20, COUNT(*) FROM notificaciones
    UNION ALL SELECT 'eventos_solicitud', 'principal', 20, COUNT(*) FROM eventos_solicitud
    UNION ALL SELECT 'roles', 'secundaria', 10, COUNT(*) FROM roles
    UNION ALL SELECT 'modulos_sistema', 'secundaria', 10, COUNT(*) FROM modulos_sistema
    UNION ALL SELECT 'modulos_x_rol', 'secundaria', 10, COUNT(*) FROM modulos_x_rol
    UNION ALL SELECT 'tipos_documento', 'secundaria', 10, COUNT(*) FROM tipos_documento
    UNION ALL SELECT 'periodos_academicos', 'secundaria', 10, COUNT(*) FROM periodos_academicos
    UNION ALL SELECT 'calificaciones_consulta', 'secundaria', 10, COUNT(*) FROM calificaciones_consulta
    UNION ALL SELECT 'password_reset_tokens', 'secundaria', 10, COUNT(*) FROM password_reset_tokens
)
SELECT tabla,
       categoria,
       minimo,
       filas,
       CASE WHEN filas >= minimo THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM conteos
ORDER BY categoria, tabla;


-- 2) FK huérfanas (24 claves foráneas de 01), todas deben dar 0 -------------
WITH huerfanas(fk, filas_huerfanas) AS (
    SELECT 'modulos_x_rol.rol_id', COUNT(*) FROM modulos_x_rol c LEFT JOIN roles p ON p.id = c.rol_id WHERE c.rol_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'modulos_x_rol.modulo_id', COUNT(*) FROM modulos_x_rol c LEFT JOIN modulos_sistema p ON p.id = c.modulo_id WHERE c.modulo_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'usuarios.rol_id', COUNT(*) FROM usuarios c LEFT JOIN roles p ON p.id = c.rol_id WHERE c.rol_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'usuarios.programa_id', COUNT(*) FROM usuarios c LEFT JOIN programas_academicos p ON p.id = c.programa_id WHERE c.programa_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'usuarios.tipo_documento_id', COUNT(*) FROM usuarios c LEFT JOIN tipos_documento p ON p.id = c.tipo_documento_id WHERE c.tipo_documento_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'zonas.sede_id', COUNT(*) FROM zonas c LEFT JOIN sedes p ON p.id = c.sede_id WHERE c.sede_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'disponibilidad_docente.docente_id', COUNT(*) FROM disponibilidad_docente c LEFT JOIN usuarios p ON p.id = c.docente_id WHERE c.docente_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'docentes_modulos.docente_id', COUNT(*) FROM docentes_modulos c LEFT JOIN usuarios p ON p.id = c.docente_id WHERE c.docente_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'docentes_modulos.modulo_id', COUNT(*) FROM docentes_modulos c LEFT JOIN modulos p ON p.id = c.modulo_id WHERE c.modulo_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'password_reset_tokens.usuario_id', COUNT(*) FROM password_reset_tokens c LEFT JOIN usuarios p ON p.id = c.usuario_id WHERE c.usuario_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'recursos_fisicos.sede_id', COUNT(*) FROM recursos_fisicos c LEFT JOIN sedes p ON p.id = c.sede_id WHERE c.sede_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'recursos_fisicos.zona_id', COUNT(*) FROM recursos_fisicos c LEFT JOIN zonas p ON p.id = c.zona_id WHERE c.zona_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'solicitudes_consultas.estudiante_id', COUNT(*) FROM solicitudes_consultas c LEFT JOIN usuarios p ON p.id = c.estudiante_id WHERE c.estudiante_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'solicitudes_consultas.docente_id', COUNT(*) FROM solicitudes_consultas c LEFT JOIN usuarios p ON p.id = c.docente_id WHERE c.docente_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'solicitudes_consultas.modulo_id', COUNT(*) FROM solicitudes_consultas c LEFT JOIN modulos p ON p.id = c.modulo_id WHERE c.modulo_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'solicitudes_consultas.recurso_fisico_id', COUNT(*) FROM solicitudes_consultas c LEFT JOIN recursos_fisicos p ON p.id = c.recurso_fisico_id WHERE c.recurso_fisico_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'calificaciones_consulta.solicitud_id', COUNT(*) FROM calificaciones_consulta c LEFT JOIN solicitudes_consultas p ON p.id = c.solicitud_id WHERE c.solicitud_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'comentarios.autor_id', COUNT(*) FROM comentarios c LEFT JOIN usuarios p ON p.id = c.autor_id WHERE c.autor_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'comentarios.solicitud_id', COUNT(*) FROM comentarios c LEFT JOIN solicitudes_consultas p ON p.id = c.solicitud_id WHERE c.solicitud_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'eventos_solicitud.solicitud_id', COUNT(*) FROM eventos_solicitud c LEFT JOIN solicitudes_consultas p ON p.id = c.solicitud_id WHERE c.solicitud_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'eventos_solicitud.usuario_id', COUNT(*) FROM eventos_solicitud c LEFT JOIN usuarios p ON p.id = c.usuario_id WHERE c.usuario_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'notificaciones.remitente_id', COUNT(*) FROM notificaciones c LEFT JOIN usuarios p ON p.id = c.remitente_id WHERE c.remitente_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'notificaciones.destinatario_id', COUNT(*) FROM notificaciones c LEFT JOIN usuarios p ON p.id = c.destinatario_id WHERE c.destinatario_id IS NOT NULL AND p.id IS NULL
    UNION ALL SELECT 'notificaciones.solicitud_consulta_id', COUNT(*) FROM notificaciones c LEFT JOIN solicitudes_consultas p ON p.id = c.solicitud_consulta_id WHERE c.solicitud_consulta_id IS NOT NULL AND p.id IS NULL
)
SELECT fk,
       filas_huerfanas,
       CASE WHEN filas_huerfanas = 0 THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM huerfanas
ORDER BY fk;


-- 3) Calificaciones SOLO sobre consultas RESUELTAS ---------------------------
SELECT COUNT(*) AS total_calificaciones,
       SUM(CASE WHEN s.estado_consulta <> 'RESUELTA' THEN 1 ELSE 0 END) AS fuera_de_resueltas,
       CASE WHEN SUM(CASE WHEN s.estado_consulta <> 'RESUELTA' THEN 1 ELSE 0 END) = 0
            THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM calificaciones_consulta c
JOIN solicitudes_consultas s ON s.id = c.solicitud_id;


-- 4) Ninguna solicitud en domingo -------------------------------------------
-- DOW = 0 es domingo en PostgreSQL. Equivalente SQLite: strftime('%w', fecha_consulta) = '0'.
SELECT COUNT(*) AS solicitudes_en_domingo,
       CASE WHEN COUNT(*) = 0 THEN 'CUMPLE' ELSE 'NO CUMPLE' END AS cumple
FROM solicitudes_consultas
WHERE EXTRACT(DOW FROM fecha_consulta) = 0;
