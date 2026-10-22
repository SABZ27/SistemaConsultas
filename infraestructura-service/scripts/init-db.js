const path = require('path');

require('dotenv').config();

const fs = require('fs');
const mysql = require('mysql2/promise');

// Proveedores externos que se siembran. La url_base es la de la API publica.
const SERVICIOS = [
  {
    nombre: 'Nager.Date',
    url_base: 'https://date.nager.at/api/v4',
    descripcion: 'API pública de festivos por país',
  },
  {
    nombre: 'Brevo',
    url_base: 'https://api.brevo.com/v3',
    descripcion: 'API de correo transaccional',
  },
];

// Tablas de la infraestructura fisica que ahora viven en PostgreSQL (FastAPI).
const TABLAS_LEGACY = ['sedes', 'zonas', 'recursos_fisicos'];

const ARGUMENTO_DROP_LEGACY = '--drop-legacy';

async function main() {
  const host = process.env.DB_HOST || '127.0.0.1';
  const port = Number(process.env.DB_PORT || 3306);
  const user = process.env.DB_USER || 'root';
  const password = process.env.DB_PASSWORD || '';
  const database = process.env.DB_NAME || 'sistema_consultas_infra';
  const ssl =
    String(process.env.DB_SSL || '').trim().toLowerCase() === 'true'
      ? { ssl: { rejectUnauthorized: false } }
      : {};

  const admin = await mysql.createConnection({ host, port, user, password, multipleStatements: true, ...ssl });
  await admin.query(
    `CREATE DATABASE IF NOT EXISTS \`${database}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
  );
  await admin.end();

  const conexion = await mysql.createConnection({
    host,
    port,
    user,
    password,
    database,
    multipleStatements: true,
    ...ssl,
  });
  const sql = fs.readFileSync(path.join(__dirname, '..', 'sql', 'schema.sql'), 'utf8');
  await conexion.query(sql);

  for (const servicio of SERVICIOS) {
    await conexion.query(
      `INSERT INTO servicios_externos (nombre, url_base, descripcion, estado)
       VALUES (?, ?, ?, 1)
       ON DUPLICATE KEY UPDATE url_base = VALUES(url_base), descripcion = VALUES(descripcion)`,
      [servicio.nombre, servicio.url_base, servicio.descripcion]
    );
  }

  const eliminarLegacy = process.argv.includes(ARGUMENTO_DROP_LEGACY);
  if (eliminarLegacy) {
    await conexion.query('SET FOREIGN_KEY_CHECKS = 0');
    for (const tabla of TABLAS_LEGACY) {
      await conexion.query(`DROP TABLE IF EXISTS \`${tabla}\``);
    }
    await conexion.query('SET FOREIGN_KEY_CHECKS = 1');
  }

  await conexion.end();

  console.log(`Esquema de servicios externos creado en ${database} (${host}:${port}).`);
  console.log(`Servicios sembrados: ${SERVICIOS.map((s) => s.nombre).join(', ')}.`);
  if (eliminarLegacy) {
    console.log(`Tablas legacy eliminadas: ${TABLAS_LEGACY.join(', ')}.`);
  }
}

main().catch((error) => {
  console.error('No se pudo inicializar la base de datos de servicios externos:', error.message);
  process.exit(1);
});
