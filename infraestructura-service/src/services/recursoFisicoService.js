const recursoRepository = require('../repositories/recursoFisicoRepository');
const sedeRepository = require('../repositories/sedeRepository');
const zonaRepository = require('../repositories/zonaRepository');
const recursoMapper = require('../mappers/recursoFisicoMapper');
const { noEncontrado, solicitudInvalida, traducirDuplicado } = require('../utils/errores');

const TIPO_POR_DEFECTO = 'SALON';
const MENSAJE_DUPLICADO =
  'Ya existe un recurso físico activo con ese nombre en la sede o zona indicada.';

async function asegurarSedeActiva(sedeId) {
  const sede = await sedeRepository.buscarPorId(sedeId);
  if (!sede) {
    throw noEncontrado('Sede no encontrada.');
  }
  return sede;
}

async function validarZona(sede, zonaId) {
  if (sede.tipo_estructura === 'SALONES') {
    if (zonaId !== undefined && zonaId !== null) {
      throw solicitudInvalida(
        'La sede es de tipo SALONES y no admite zonas; el recurso no puede tener zonaId.'
      );
    }
    return null;
  }

  if (zonaId === undefined || zonaId === null) {
    throw solicitudInvalida(
      `La sede es de tipo ${sede.tipo_estructura} y el recurso requiere zonaId de esa sede.`
    );
  }

  const zona = await zonaRepository.buscarPorId(zonaId);
  if (!zona) {
    throw solicitudInvalida('La zona indicada no existe o está inactiva.');
  }
  if (zona.sede_id !== sede.id) {
    throw solicitudInvalida('La zona indicada no pertenece a la sede del recurso.');
  }
  return zona;
}

async function listar({ sedeId, zonaId, incluirInactivos = false } = {}) {
  const filas = await recursoRepository.listar({ sedeId, zonaId, incluirInactivos });
  return filas.map(recursoMapper.aRespuesta);
}

async function listarPorSede(sedeId, { incluirInactivos = false } = {}) {
  await asegurarSedeActiva(sedeId);
  return listar({ sedeId, incluirInactivos });
}

async function listarPorZona(zonaId, { incluirInactivos = false } = {}) {
  const zona = await zonaRepository.buscarPorId(zonaId);
  if (!zona) {
    throw noEncontrado('Zona no encontrada.');
  }
  return listar({ zonaId, incluirInactivos });
}

async function obtener(id, { incluirInactivos = false } = {}) {
  const fila = await recursoRepository.buscarPorId(id, { incluirInactivos });
  if (!fila) {
    throw noEncontrado('Recurso físico no encontrado.');
  }
  return recursoMapper.aRespuesta(fila);
}

async function crear({ sedeId, zonaId, nombre, tipo }) {
  const sede = await asegurarSedeActiva(sedeId);
  await validarZona(sede, zonaId);
  try {
    const id = await recursoRepository.crear({
      sedeId,
      zonaId: zonaId ?? null,
      nombre,
      tipo: tipo || TIPO_POR_DEFECTO,
    });
    return await obtener(id);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
}

async function actualizar(id, datos) {
  const actual = await recursoRepository.buscarPorId(id);
  if (!actual) {
    throw noEncontrado('Recurso físico no encontrado.');
  }

  const sede = await asegurarSedeActiva(actual.sede_id);
  const zonaIdFinal = Object.prototype.hasOwnProperty.call(datos, 'zonaId')
    ? datos.zonaId
    : actual.zona_id;
  await validarZona(sede, zonaIdFinal);

  try {
    await recursoRepository.actualizar(id, {
      sedeId: actual.sede_id,
      zonaId: zonaIdFinal ?? null,
      nombre: datos.nombre,
      tipo: datos.tipo || actual.tipo,
    });
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
  return obtener(id);
}

async function desactivar(id) {
  const recurso = await recursoRepository.buscarPorId(id);
  if (!recurso) {
    throw noEncontrado('Recurso físico no encontrado.');
  }
  await recursoRepository.cambiarEstado(id, false);
}

async function activar(id) {
  const recurso = await recursoRepository.buscarPorIdSinEstado(id);
  if (!recurso) {
    throw noEncontrado('Recurso físico no encontrado.');
  }
  if (recurso.estado) {
    return recursoMapper.aRespuesta(recurso);
  }
  try {
    await recursoRepository.cambiarEstado(id, true);
  } catch (error) {
    throw traducirDuplicado(error, MENSAJE_DUPLICADO);
  }
  return obtener(id);
}

module.exports = {
  listar,
  listarPorSede,
  listarPorZona,
  obtener,
  crear,
  actualizar,
  desactivar,
  activar,
};
