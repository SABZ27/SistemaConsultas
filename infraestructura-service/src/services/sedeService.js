const sedeRepository = require('../repositories/sedeRepository');
const sedeMapper = require('../mappers/sedeMapper');
const { noEncontrado, solicitudInvalida, traducirDuplicado } = require('../utils/errores');

const MENSAJE_DUPLICADO = 'Ya existe una sede activa con ese nombre.';

async function listar({ incluirInactivos = false } = {}) {
  const filas = await sedeRepository.listar({ incluirInactivos });
  return filas.map(sedeMapper.aRespuesta);
}

async function obtener(id, { incluirInactivos = false } = {}) {
  const fila = await sedeRepository.buscarPorId(id, { incluirInactivos });
  if (!fila) {
    throw noEncontrado('Sede no encontrada.');
  }
  return sedeMapper.aRespuesta(fila);
}

async function crear(datos) {
  try {
    const id = await sedeRepository.crear(datos);
    return await obtener(id);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
}

async function actualizar(id, datos) {
  const sede = await sedeRepository.buscarPorId(id);
  if (!sede) {
    throw noEncontrado('Sede no encontrada.');
  }

  if (datos.tipoEstructura !== sede.tipo_estructura) {
    const zonas = await sedeRepository.contarZonasActivas(id);
    const recursos = await sedeRepository.contarRecursosActivos(id);
    if (zonas > 0 || recursos > 0) {
      throw solicitudInvalida(
        'No se puede cambiar el tipo de estructura de una sede con zonas o recursos físicos activos.'
      );
    }
  }

  try {
    await sedeRepository.actualizar(id, datos);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
  return obtener(id);
}

async function desactivar(id) {
  const sede = await sedeRepository.buscarPorId(id);
  if (!sede) {
    throw noEncontrado('Sede no encontrada.');
  }

  const zonas = await sedeRepository.contarZonasActivas(id);
  if (zonas > 0) {
    throw solicitudInvalida('No se puede desactivar una sede con zonas activas.');
  }

  const recursos = await sedeRepository.contarRecursosActivos(id);
  if (recursos > 0) {
    throw solicitudInvalida('No se puede desactivar una sede con recursos físicos activos.');
  }

  await sedeRepository.cambiarEstado(id, false);
}

async function activar(id) {
  const sede = await sedeRepository.buscarPorIdSinEstado(id);
  if (!sede) {
    throw noEncontrado('Sede no encontrada.');
  }
  if (sede.estado) {
    return sedeMapper.aRespuesta(sede);
  }
  try {
    await sedeRepository.cambiarEstado(id, true);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
  return obtener(id);
}

module.exports = { listar, obtener, crear, actualizar, desactivar, activar };
