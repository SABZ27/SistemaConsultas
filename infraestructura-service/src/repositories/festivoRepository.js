const pool = require('../config/database');

const CAMPOS =
  "id, servicio_id, consulta_servicio_id, DATE_FORMAT(fecha, '%Y-%m-%d') AS fecha, pais, nombre, anio, estado";

// Cache local de los festivos: las lecturas solo devuelven los activos y
// siempre filtran por pais y anio.
async function listarActivosPorAnio(pais, anio) {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM festivos
      WHERE estado = 1 AND pais = ? AND anio = ?
      ORDER BY fecha`,
    [pais, anio]
  );
  return filas;
}

// Existe alguna fila del ano (activa o inactiva). Sirve para no volver a
// sincronizar con Nager.Date cuando lo unico que hay son filas desactivadas.
async function existeAlgunoDelAnio(pais, anio) {
  const [filas] = await pool.query(
    'SELECT 1 AS ok FROM festivos WHERE pais = ? AND anio = ? LIMIT 1',
    [pais, anio]
  );
  return filas.length > 0;
}

async function buscarActivoPorFecha(pais, fecha) {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM festivos
      WHERE estado = 1 AND pais = ? AND fecha = ?
      LIMIT 1`,
    [pais, fecha]
  );
  return filas[0] || null;
}

async function buscarPorId(id) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} FROM festivos WHERE id = ? LIMIT 1`, [id]);
  return filas[0] || null;
}

// El upsert usa el unico UNIQUE (fecha, pais) y NUNCA cambia estado: un
// festivo desactivado no se resucita al resincronizar.
async function guardarVarios(filas) {
  if (!filas || filas.length === 0) {
    return;
  }
  const valores = filas.map(() => '(?, ?, ?, ?, ?, ?)').join(', ');
  const params = filas.flatMap((fila) => [
    fila.servicioId,
    fila.consultaServicioId,
    fila.fecha,
    fila.pais,
    fila.nombre,
    fila.anio,
  ]);
  await pool.query(
    `INSERT INTO festivos (servicio_id, consulta_servicio_id, fecha, pais, nombre, anio)
     VALUES ${valores}
     ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), anio = VALUES(anio)`,
    params
  );
}

// Borrado logico: estado = 0.
async function desactivar(id) {
  const [resultado] = await pool.query('UPDATE festivos SET estado = 0 WHERE id = ? AND estado = 1', [
    id,
  ]);
  return resultado.affectedRows > 0;
}

module.exports = {
  listarActivosPorAnio,
  existeAlgunoDelAnio,
  buscarActivoPorFecha,
  buscarPorId,
  guardarVarios,
  desactivar,
};
