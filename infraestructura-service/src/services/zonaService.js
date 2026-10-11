const zonaRepository = require('../repositories/zonaRepository');
const sedeRepository = require('../repositories/sedeRepository');
const zonaMapper = require('../mappers/zonaMapper');
const { noEncontrado, solicitudInvalida, traducirDuplicado } = require('../utils/errores');

const MENSAJE_DUPLICADO = 'Ya existe una zona activa con ese nombre en la sede.';

async function asegurarSedeActiva(sedeId) {
  const sede = await sedeRepository.buscarPorId(sedeId);
  if (!sede) {
    throw noEncontrado('Sede no encontrada.');
  }
  return sede;
}

async function listar({ sedeId, incluirInactivos = false } = {}) {
  const filas = await zonaRepository.listar({ sedeId, incluirInactivos });
  return filas.map(zonaMapper.aRespuesta);
}

async function listarPorSede(sedeId, { incluirInactivos = false } = {}) {
  await asegurarSedeActiva(sedeId);
  return listar({ sedeId, incluirInactivos });
}

async function obtener(id, { incluirInactivos = false } = {}) {
  const fila = await zonaRepository.buscarPorId(id, { incluirInactivos });
  if (!fila) {
    throw noEncontrado('Zona no encontrada.');
  }
  return zonaMapper.aRespuesta(fila);
}

async function crear({ sedeId, nombre }) {
  const sede = await asegurarSedeActiva(sedeId);
  if (sede.tipo_estructura === 'SALONES') {
    throw solicitudInvalida(
      'La sede es de tipo SALONES y no admite zonas; los recursos cuelgan directamente de la sede.'
    );
  }
  try {
    const id = await zonaRepository.crear({ sedeId, nombre });
    return await obtener(id);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
}

async function actualizar(id, { nombre }) {
  const zona = await zonaRepository.buscarPorId(id);
  if (!zona) {
    throw noEncontrado('Zona no encontrada.');
  }
  try {
    await zonaRepository.actualizar(id, { nombre });
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
  return obtener(id);
}

async function desactivar(id) {
  const zona = await zonaRepository.buscarPorId(id);
  if (!zona) {
    throw noEncontrado('Zona no encontrada.');
  }
  const recursos = await zonaRepository.contarRecursosActivos(id);
  if (recursos > 0) {
    throw solicitudInvalida('No se puede desactivar una zona con recursos físicos activos.');
  }
  await zonaRepository.cambiarEstado(id, false);
}

async function activar(id) {
  const zona = await zonaRepository.buscarPorIdSinEstado(id);
  if (!zona) {
    throw noEncontrado('Zona no encontrada.');
  }
  if (zona.estado) {
    return zonaMapper.aRespuesta(zona);
  }
  try {
    await zonaRepository.cambiarEstado(id, true);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
  return obtener(id);
}

module.exports = { listar, listarPorSede, obtener, crear, actualizar, desactivar, activar };
