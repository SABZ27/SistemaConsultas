const pool = require('../config/database');

const CAMPOS = 'id, nombre, tipo_estructura, estado, creado, actualizado';

async function listar({ incluirInactivos = false } = {}) {
  const where = incluirInactivos ? '' : 'WHERE estado = 1';
  const [filas] = await pool.query(`SELECT ${CAMPOS} FROM sedes ${where} ORDER BY nombre`);
  return filas;
}

async function buscarPorId(id, { incluirInactivos = false } = {}) {
  const condicion = incluirInactivos ? 'id = ?' : 'id = ? AND estado = 1';
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM sedes WHERE ${condicion} LIMIT 1`,
    [id]
  );
  return filas[0] || null;
}

async function buscarPorIdSinEstado(id) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} FROM sedes WHERE id = ? LIMIT 1`, [id]);
  return filas[0] || null;
}

async function crear({ nombre, tipoEstructura }) {
  const [resultado] = await pool.query(
    'INSERT INTO sedes (nombre, tipo_estructura) VALUES (?, ?)',
    [nombre, tipoEstructura]
  );
  return resultado.insertId;
}

async function actualizar(id, { nombre, tipoEstructura }) {
  await pool.query('UPDATE sedes SET nombre = ?, tipo_estructura = ? WHERE id = ?', [
    nombre,
    tipoEstructura,
    id,
  ]);
}

async function cambiarEstado(id, estado) {
  await pool.query('UPDATE sedes SET estado = ? WHERE id = ?', [estado ? 1 : 0, id]);
}

async function contarZonasActivas(sedeId) {
  const [filas] = await pool.query(
    'SELECT COUNT(*) AS total FROM zonas WHERE sede_id = ? AND estado = 1',
    [sedeId]
  );
  return Number(filas[0].total);
}

async function contarRecursosActivos(sedeId) {
  const [filas] = await pool.query(
    'SELECT COUNT(*) AS total FROM recursos_fisicos WHERE sede_id = ? AND estado = 1',
    [sedeId]
  );
  return Number(filas[0].total);
}

module.exports = {
  listar,
  buscarPorId,
  buscarPorIdSinEstado,
  crear,
  actualizar,
  cambiarEstado,
  contarZonasActivas,
  contarRecursosActivos,
};
