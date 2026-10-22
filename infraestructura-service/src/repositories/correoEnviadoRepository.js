const pool = require('../config/database');

async function registrar({
  servicioId,
  consultaServicioId,
  destinatario,
  asunto,
  estadoEnvio,
  respuestaProveedor = null,
}) {
  const [resultado] = await pool.query(
    `INSERT INTO correos_enviados
       (servicio_id, consulta_servicio_id, destinatario, asunto, estado_envio, respuesta_proveedor)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [
      servicioId,
      consultaServicioId,
      destinatario,
      asunto,
      estadoEnvio,
      respuestaProveedor ? String(respuestaProveedor).slice(0, 255) : null,
    ]
  );
  return resultado.insertId;
}

module.exports = { registrar };
