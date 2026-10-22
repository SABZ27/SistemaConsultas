-- Siembra idempotente de los proveedores externos.
-- Se ejecuta despues de sql/schema.sql (docker-entrypoint-initdb.d) o con
-- `npm run db:init`, que ademas normaliza la url_base y la descripcion.
INSERT INTO servicios_externos (nombre, url_base, descripcion, estado)
VALUES
  ('Nager.Date', 'https://date.nager.at/api/v4', 'API pública de festivos por país', 1),
  ('Brevo', 'https://api.brevo.com/v3', 'API de correo transaccional', 1)
ON DUPLICATE KEY UPDATE
  url_base = VALUES(url_base),
  descripcion = VALUES(descripcion);
