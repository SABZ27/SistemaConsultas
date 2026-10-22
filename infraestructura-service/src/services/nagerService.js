const crypto = require('crypto');

const env = require('../config/env');
const consultaRepository = require('../repositories/consultaServicioExternoRepository');
const festivoRepository = require('../repositories/festivoRepository');
const servicioExternoService = require('./servicioExternoService');
const { httpGet } = require('../utils/http');
const { AppError } = require('../utils/errores');
const { detalleBreve } = require('../utils/sanear');
const { nombreEnEspanol } = require('../utils/nombresFestivos');
const { ajustarLeyEmiliani } = require('../utils/leyEmiliani');

// API documentada: GET {url_base}/Holidays/{CountryCode}/{Year}
// Colombia esta cubierta en https://date.nager.at/country/coverage y la v4 es
// la version oficial (https://date.nager.at/api).
function construirEndpoint(urlBase, pais, anio) {
  return `${String(urlBase).replace(/\/+$/, '')}/Holidays/${pais}/${anio}`;
}

// Descarga el calendario del ano, deja la llamada registrada en la bitacora y
// guarda los festivos en la cache local.
async function sincronizar(anio, pais) {
  const servicio = await servicioExternoService.obtenerActivo(servicioExternoService.NOMBRE_NAGER);
  const endpoint = construirEndpoint(servicio.url_base, pais, anio);

  let resultado = { ok: false, status: 0, datos: null, duracionMs: 0 };
  let errorRed = null;
  try {
    resultado = await httpGet(endpoint);
  } catch (error) {
    errorRed = error;
  }

  // La llamada se registra siempre, incluso si no hubo respuesta por red.
  const consultaId = await consultaRepository.registrar({
    servicioId: servicio.id,
    referencia: crypto.randomUUID(),
    endpoint,
    codigoHttp: errorRed ? null : resultado.status,
    exito: resultado.ok,
    duracionMs: resultado.duracionMs,
    detalle: detalleBreve(
      errorRed ? 'sin respuesta' : resultado.ok ? `festivos de ${pais} ${anio}` : `HTTP ${resultado.status}`
    ),
  });

  if (errorRed || !resultado.ok) {
    throw new AppError(502, 'El proveedor de festivos no respondió correctamente.');
  }

  const holidays = Array.isArray(resultado.datos) ? resultado.datos : [];
  const filas = holidays
    .filter((festivo) => festivo && festivo.date && festivo.name)
    .map((festivo) => {
      // Correccion Ley Emiliani: Ascension Day y Corpus Christi se observan el
      // lunes siguiente en Colombia (ver src/utils/leyEmiliani.js).
      const { fecha, anio: anioFinal } = ajustarLeyEmiliani({
        fecha: festivo.date,
        nombre: festivo.name,
      });
      return {
        servicioId: servicio.id,
        consultaServicioId: consultaId,
        fecha,
        pais,
        nombre: nombreEnEspanol(festivo.name) || festivo.name,
        anio: anioFinal,
      };
    });

  await festivoRepository.guardarVarios(filas);
  return festivoRepository.listarActivosPorAnio(pais, anio);
}

module.exports = { sincronizar, construirEndpoint };
