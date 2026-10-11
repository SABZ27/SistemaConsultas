const path = require('path');

require('dotenv').config();

const fs = require('fs');
const mysql = require('mysql2/promise');

async function main() {
  const host = process.env.DB_HOST || '127.0.0.1';
  const port = Number(process.env.DB_PORT || 3306);
  const user = process.env.DB_USER || 'root';
  const password = process.env.DB_PASSWORD || '';
  const database = process.env.DB_NAME || 'sistema_consultas_infra';

  const admin = await mysql.createConnection({ host, port, user, password, multipleStatements: true });
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
  });
  const sql = fs.readFileSync(path.join(__dirname, '..', 'sql', 'schema.sql'), 'utf8');
  await conexion.query(sql);
  await conexion.end();

  console.log(`Esquema de infraestructura creado en ${database} (${host}:${port}).`);
}

main().catch((error) => {
  console.error('No se pudo inicializar la base de datos de infraestructura:', error.message);
  process.exit(1);
});
