const pool = require('../config/database');

// Bitacora de las llamadas a proveedores externos. Cada llamada externa
// inserta una fila y devuelve su id, que despues referencian las filas de
// festivos (consulta_servicio_id) y de correos_enviados (consulta_servicio_id).
async function registrar({
  servicioId,
  referencia,
  endpoint,
  codigoHttp = null,
  exito = false,
  duracionMs = null,
  detalle = null,
}) {
  const [resultado] = await pool.query(
    `INSERT INTO consultas_servicio_externo
       (servicio_id, referencia, endpoint, codigo_http, exito, duracion_ms, detalle)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [
      servicioId,
      referencia,
      endpoint,
      codigoHttp,
      exito ? 1 : 0,
      duracionMs,
      detalle ? String(detalle).slice(0, 255) : null,
    ]
  );
  return resultado.insertId;
}

module.exports = { registrar };
