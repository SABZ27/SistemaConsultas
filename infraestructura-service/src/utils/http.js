const env = require('../config/env');
const { AppError } = require('./errores');

// Envoltura minima sobre fetch: timeout con AbortController, parseo JSON
// tolerante y normalizacion de los errores de red en AppError (502).
async function peticion(url, { metodo = 'GET', cuerpo = null, cabeceras = {}, timeoutMs } = {}) {
  const limite = timeoutMs || env.externos.httpTimeoutMs;
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), limite);
  const inicio = Date.now();
  try {
    const respuesta = await fetch(url, {
      method: metodo,
      headers: { Accept: 'application/json', ...cabeceras },
      body: cuerpo === null ? undefined : JSON.stringify(cuerpo),
      signal: controlador.signal,
    });
    const duracionMs = Date.now() - inicio;
    const texto = await respuesta.text();
    let datos = null;
    if (texto) {
      try {
        datos = JSON.parse(texto);
      } catch {
        datos = null;
      }
    }
    return { ok: respuesta.ok, status: respuesta.status, datos, duracionMs, texto };
  } catch {
    throw new AppError(502, 'No se pudo contactar al proveedor externo.');
  } finally {
    clearTimeout(temporizador);
  }
}

// GET con 1 reintento (errores de red y respuestas 5xx). Se usa solo para
// Nager.Date: leer el calendario es idempotente y el proveedor puede estar
// despertando frio.
async function httpGet(url, opciones = {}) {
  const intentos = 2;
  let ultimoResultado = null;

  for (let intento = 1; intento <= intentos; intento += 1) {
    let resultado;
    try {
      resultado = await peticion(url, { ...opciones, metodo: 'GET' });
    } catch (error) {
      // Error de red: se reintenta una vez.
      if (intento === intentos) {
        throw error;
      }
      continue;
    }
    if (resultado.ok || resultado.status < 500) {
      return resultado;
    }
    ultimoResultado = resultado; // 5xx: se reintenta
  }

  return ultimoResultado;
}

// POST sin reintentos: reenviar un correo puede duplicar el envio.
async function httpPost(url, cuerpo, cabeceras = {}) {
  return peticion(url, { metodo: 'POST', cuerpo, cabeceras });
}

module.exports = { peticion, httpGet, httpPost };
