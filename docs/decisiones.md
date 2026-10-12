# Decisiones de diseño

## Módulos vs módulos_sistema
Se mantiene separación conceptual: modulos_sistema define los módulos disponibles en la aplicación y modulos_x_rol controla permisos por rol. La lógica de autorización usa esta matriz.

## Borrado lógico y estado
Todas las entidades relevantes utilizan borrado lógico mediante columna estado (boolean/bit) en lugar de DELETE físico, permitiendo trazabilidad e integridad histórica.

## estado_consulta
Las solicitudes de consulta gestionan su estado a través del enum/valor estado_consulta, con transiciones controladas por reglas de negocio.

## JWT con rol y módulos
El token JWT incluye ol y modulos permitidos para el usuario, utilizado por middlewares/decoradores de autorización.

## Estructuras de sede BLOQUES/SALONES/PISOS
La infraestructura física se organiza jerárquicamente: Sede → Bloque → Recurso físico. Tipificación según reglas BLOQUES/SALONES/PISOS cuando aplica.

## Referencia sin FK entre servicios y copia de la ubicación
Para desacoplar servicios, no se crean FK entre dominios distribuidos (ej. infraestructura). Cuando se asigna un recurso físico desde el servicio de infraestructura, se copia ecurso_fisico_nombre (ubicación completa) en solicitudes_consultas, preservando historial.

## Únicos parciales
Se utilizan índices únicos parciales (WHERE estado = true/1) para garantizar unicidad entre registros activos sin afectar históricos.
