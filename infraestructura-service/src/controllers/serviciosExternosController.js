const servicioExternoService = require('../services/servicioExternoService');
const asyncHandler = require('../utils/asyncHandler');

function aRespuesta(fila) {
  return {
    id: fila.id,
    nombre: fila.nombre,
    urlBase: fila.url_base,
    descripcion: fila.descripcion,
  };
}

const listar = asyncHandler(async (_req, res) => {
  const filas = await servicioExternoService.listar();
  res.json(filas.map(aRespuesta));
});

module.exports = { listar };
