const pool = require('../config/database');

const CAMPOS = 'id, nombre, url_base, descripcion, estado, creado, actualizado';

async function listarActivos() {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM servicios_externos WHERE estado = 1 ORDER BY nombre`
  );
  return filas;
}

// La busqueda es por nombre (clave logica del proveedor): 'Nager.Date' o 'Brevo'.
async function buscarActivoPorNombre(nombre) {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM servicios_externos WHERE nombre = ? AND estado = 1 LIMIT 1`,
    [nombre]
  );
  return filas[0] || null;
}

module.exports = { listarActivos, buscarActivoPorNombre };
