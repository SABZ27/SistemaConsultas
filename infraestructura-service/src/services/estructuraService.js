const sedeRepository = require('../repositories/sedeRepository');
const zonaRepository = require('../repositories/zonaRepository');
const recursoRepository = require('../repositories/recursoFisicoRepository');
const sedeMapper = require('../mappers/sedeMapper');
const zonaMapper = require('../mappers/zonaMapper');
const recursoMapper = require('../mappers/recursoFisicoMapper');
const { noEncontrado } = require('../utils/errores');

async function obtenerEstructura(id) {
  const sede = await sedeRepository.buscarPorId(id);
  if (!sede) {
    throw noEncontrado('Sede no encontrada.');
  }

  const base = sedeMapper.aRespuesta(sede);

  if (sede.tipo_estructura === 'SALONES') {
    const filasRecursos = await recursoRepository.listar({ sedeId: id });
    const recursos = filasRecursos.map(recursoMapper.aRespuesta);
    return { ...base, zonas: [], recursos };
  }

  const filasZonas = await zonaRepository.listar({ sedeId: id });
  const zonas = [];
  for (const filaZona of filasZonas) {
    const filasRecursos = await recursoRepository.listar({ zonaId: filaZona.id });
    const recursos = filasRecursos.map(recursoMapper.aRespuesta);
    zonas.push(zonaMapper.aRespuestaConRecursos(filaZona, recursos));
  }

  return { ...base, zonas, recursos: [] };
}

module.exports = { obtenerEstructura };
