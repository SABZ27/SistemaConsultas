const pool = require('../config/database');

const CAMPOS = `
  z.id, z.sede_id, z.nombre, z.estado, z.creado, z.actualizado,
  s.nombre AS sede_nombre
`;

async function listar({ sedeId, incluirInactivos = false } = {}) {
  const condiciones = [];
  const parametros = [];
  if (sedeId !== undefined && sedeId !== null) {
    condiciones.push('z.sede_id = ?');
    parametros.push(sedeId);
  }
  if (!incluirInactivos) {
    condiciones.push('z.estado = 1');
  }
  const where = condiciones.length ? `WHERE ${condiciones.join(' AND ')}` : '';
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM zonas z JOIN sedes s ON s.id = z.sede_id ${where} ORDER BY z.nombre`,
    parametros
  );
  return filas;
}

async function buscarPorId(id, { incluirInactivos = false } = {}) {
  const condicion = incluirInactivos ? 'z.id = ?' : 'z.id = ? AND z.estado = 1';
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM zonas z JOIN sedes s ON s.id = z.sede_id WHERE ${condicion} LIMIT 1`,
    [id]
  );
  return filas[0] || null;
}

async function buscarPorIdSinEstado(id) {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM zonas z JOIN sedes s ON s.id = z.sede_id WHERE z.id = ? LIMIT 1`,
    [id]
  );
  return filas[0] || null;
}

async function crear({ sedeId, nombre }) {
  const [resultado] = await pool.query('INSERT INTO zonas (sede_id, nombre) VALUES (?, ?)', [
    sedeId,
    nombre,
  ]);
  return resultado.insertId;
}

async function actualizar(id, { nombre }) {
  await pool.query('UPDATE zonas SET nombre = ? WHERE id = ?', [nombre, id]);
}

async function cambiarEstado(id, estado) {
  await pool.query('UPDATE zonas SET estado = ? WHERE id = ?', [estado ? 1 : 0, id]);
}

async function contarRecursosActivos(zonaId) {
  const [filas] = await pool.query(
    'SELECT COUNT(*) AS total FROM recursos_fisicos WHERE zona_id = ? AND estado = 1',
    [zonaId]
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
  contarRecursosActivos,
};
