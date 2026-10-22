const crypto = require('crypto');

const env = require('../config/env');
const consultaRepository = require('../repositories/consultaServicioExternoRepository');
const correoRepository = require('../repositories/correoEnviadoRepository');
const servicioExternoService = require('./servicioExternoService');
const { httpPost } = require('../utils/http');
const { AppError } = require('../utils/errores');
const { detalleBreve } = require('../utils/sanear');

// API HTTP de Brevo (NO SMTP): POST {url_base}/smtp/email
// Documentacion: https://developers.brevo.com/docs/send-a-transactional-email
function construirEndpoint(urlBase) {
  return `${String(urlBase).replace(/\/+$/, '')}/smtp/email`;
}

async function enviar({ para, paraNombre, asunto, contenido }) {
  const apiKey = env.email.providerApiKey;
  const remitente = env.email.from;
  if (!apiKey || !remitente) {
    throw new AppError(503, 'El proveedor de correo no está configurado.');
  }

  const servicio = await servicioExternoService.obtenerActivo(servicioExternoService.NOMBRE_BREVO);
  const endpoint = construirEndpoint(servicio.url_base);

  const cuerpo = {
    sender: { email: remitente, ...(env.email.fromName ? { name: env.email.fromName } : {}) },
    to: [{ email: para, ...(paraNombre ? { name: paraNombre } : {}) }],
    subject: asunto,
    textContent: contenido,
  };

  let resultado = { ok: false, status: 0, datos: null, duracionMs: 0 };
  let errorRed = null;
  try {
    // El POST no se reintenta: reenviar un correo puede duplicar el envio.
    resultado = await httpPost(endpoint, cuerpo, {
      'api-key': apiKey,
      'Content-Type': 'application/json',
    });
  } catch (error) {
    errorRed = error;
  }

  const exito = resultado.ok;

  // La llamada se registra siempre, incluso si no hubo respuesta por red.
  const consultaId = await consultaRepository.registrar({
    servicioId: servicio.id,
    referencia: crypto.randomUUID(),
    endpoint,
    codigoHttp: errorRed ? null : resultado.status,
    exito,
    duracionMs: resultado.duracionMs,
    detalle: detalleBreve(
      errorRed ? 'sin respuesta' : exito ? 'correo enviado' : `HTTP ${resultado.status}`
    ),
  });

  // Respuesta breve del proveedor: solo el messageId. Nunca el cuerpo del
  // correo ni la respuesta completa.
  const respuestaProveedor = exito && resultado.datos ? resultado.datos.messageId || null : null;

  const id = await correoRepository.registrar({
    servicioId: servicio.id,
    consultaServicioId: consultaId,
    destinatario: para,
    asunto,
    estadoEnvio: exito ? 'ENVIADO' : 'FALLIDO',
    respuestaProveedor,
  });

  if (!exito) {
    throw new AppError(502, 'No se pudo enviar el correo.');
  }

  return { id, messageId: respuestaProveedor, estadoEnvio: 'ENVIADO' };
}

module.exports = { enviar, construirEndpoint };
