const pool = require('../config/database');

const CAMPOS = `
  r.id, r.sede_id, r.zona_id, r.nombre, r.tipo, r.estado, r.creado, r.actualizado,
  s.nombre AS sede_nombre, z.nombre AS zona_nombre
`;

const BASE = `FROM recursos_fisicos r
  JOIN sedes s ON s.id = r.sede_id
  LEFT JOIN zonas z ON z.id = r.zona_id`;

async function listar({ sedeId, zonaId, incluirInactivos = false } = {}) {
  const condiciones = [];
  const parametros = [];
  if (sedeId !== undefined && sedeId !== null) {
    condiciones.push('r.sede_id = ?');
    parametros.push(sedeId);
  }
  if (zonaId !== undefined && zonaId !== null) {
    condiciones.push('r.zona_id = ?');
    parametros.push(zonaId);
  }
  if (!incluirInactivos) {
    condiciones.push('r.estado = 1');
  }
  const where = condiciones.length ? `WHERE ${condiciones.join(' AND ')}` : '';
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} ${BASE} ${where} ORDER BY r.nombre`,
    parametros
  );
  return filas;
}

async function buscarPorId(id, { incluirInactivos = false } = {}) {
  const condicion = incluirInactivos ? 'r.id = ?' : 'r.id = ? AND r.estado = 1';
  const [filas] = await pool.query(`SELECT ${CAMPOS} ${BASE} WHERE ${condicion} LIMIT 1`, [id]);
  return filas[0] || null;
}

async function buscarPorIdSinEstado(id) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} ${BASE} WHERE r.id = ? LIMIT 1`, [id]);
  return filas[0] || null;
}

async function crear({ sedeId, zonaId, nombre, tipo }) {
  const [resultado] = await pool.query(
    'INSERT INTO recursos_fisicos (sede_id, zona_id, nombre, tipo) VALUES (?, ?, ?, ?)',
    [sedeId, zonaId ?? null, nombre, tipo]
  );
  return resultado.insertId;
}

async function actualizar(id, { sedeId, zonaId, nombre, tipo }) {
  await pool.query(
    'UPDATE recursos_fisicos SET sede_id = ?, zona_id = ?, nombre = ?, tipo = ? WHERE id = ?',
    [sedeId, zonaId ?? null, nombre, tipo, id]
  );
}

async function cambiarEstado(id, estado) {
  await pool.query('UPDATE recursos_fisicos SET estado = ? WHERE id = ?', [estado ? 1 : 0, id]);
}

module.exports = {
  listar,
  buscarPorId,
  buscarPorIdSinEstado,
  crear,
  actualizar,
  cambiarEstado,
};
