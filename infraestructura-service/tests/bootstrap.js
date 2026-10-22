const fs = require('fs');
const path = require('path');

const mysql = require('mysql2/promise');

const { asegurarNombreDePrueba } = require('./testEnv');

let promesa = null;

// Crea (si hace falta) la base del worker actual y aplica el esquema. Es
// idempotente: varias ejecuciones en el mismo worker reutilizan la promesa y,
// aun así, el resultado es el mismo.
function asegurarBaseDePrueba() {
  if (promesa) {
    return promesa;
  }

  promesa = (async () => {
    const host = process.env.DB_HOST;
    const port = Number(process.env.DB_PORT);
    const user = process.env.DB_USER;
    const password = process.env.DB_PASSWORD;
    const database = process.env.DB_NAME;

    asegurarNombreDePrueba(database);

    const admin = await mysql.createConnection({ host, port, user, password });
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
    await conexion.query('SET FOREIGN_KEY_CHECKS = 0');
    await conexion.query(
      'DROP TABLE IF EXISTS correos_enviados, festivos, consultas_servicio_externo, servicios_externos'
    );
    await conexion.query(
      'DROP TABLE IF EXISTS recursos_fisicos, zonas, sedes'
    );
    await conexion.query('SET FOREIGN_KEY_CHECKS = 1');

    const sql = fs.readFileSync(path.join(__dirname, '..', 'sql', 'schema.sql'), 'utf8');
    await conexion.query(sql);
    await conexion.end();

    return database;
  })();

  return promesa;
}

module.exports = { asegurarBaseDePrueba };
