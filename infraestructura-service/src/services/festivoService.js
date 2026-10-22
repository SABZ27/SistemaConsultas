const festivoRepository = require('../repositories/festivoRepository');
const nagerService = require('./nagerService');
const { noEncontrado } = require('../utils/errores');
const { ajustarLeyEmiliani } = require('../utils/leyEmiliani');

function aRespuesta(fila) {
  return {
    id: fila.id,
    fecha: fila.fecha,
    pais: fila.pais,
    anio: fila.anio,
    nombre: fila.nombre,
    tipo: null,
  };
}

// Cache local: si el ano ya esta sincronizado no se vuelve a llamar a
// Nager.Date. Si lo unico que hay son filas desactivadas tampoco se
// resincroniza (y el upsert nunca cambia el estado).
async function obtenerFestivos(anio, pais) {
  const filas = await festivoRepository.listarActivosPorAnio(pais, anio);
  if (filas.length > 0) {
    return filas;
  }
  if (await festivoRepository.existeAlgunoDelAnio(pais, anio)) {
    return filas;
  }
  return nagerService.sincronizar(anio, pais);
}

async function listar(anio, pais) {
  const filas = await obtenerFestivos(anio, pais);
  return filas.map(aRespuesta);
}

async function validar(fecha, pais) {
  let festivo = await festivoRepository.buscarActivoPorFecha(pais, fecha);

  if (!festivo) {
    const anio = Number(String(fecha).slice(0, 4));
    if (Number.isInteger(anio)) {
      await obtenerFestivos(anio, pais);
      festivo = await festivoRepository.buscarActivoPorFecha(pais, fecha);
    }
  }

  if (!festivo) {
    return { fecha, pais, esFestivo: false, nombre: null, id: null };
  }

  return {
    id: festivo.id,
    fecha: festivo.fecha,
    pais: festivo.pais,
    esFestivo: true,
    nombre: festivo.nombre,
  };
}

// Borrado logico del festivo (estado = 0).
async function desactivar(id) {
  const festivo = await festivoRepository.buscarPorId(id);
  if (!festivo || !festivo.estado) {
    throw noEncontrado('Festivo no encontrado.');
  }
  const ok = await festivoRepository.desactivar(id);
  if (!ok) {
    throw noEncontrado('Festivo no encontrado.');
  }
}

module.exports = { listar, validar, desactivar, aRespuesta, ajustarLeyEmiliani };
