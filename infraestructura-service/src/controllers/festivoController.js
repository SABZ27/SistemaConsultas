const festivoService = require('../services/festivoService');
const asyncHandler = require('../utils/asyncHandler');
const env = require('../config/env');
const { solicitudInvalida } = require('../utils/errores');

function paisPorDefecto(req) {
  return (req.datos && req.datos.pais) || env.externos.nagerPais;
}

const listar = asyncHandler(async (req, res) => {
  res.json(await festivoService.listar(req.datos.anio, paisPorDefecto(req)));
});

const validar = asyncHandler(async (req, res) => {
  res.json(await festivoService.validar(req.datos.fecha, paisPorDefecto(req)));
});

const desactivar = asyncHandler(async (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id <= 0) {
    throw solicitudInvalida('El identificador del festivo no es válido.');
  }
  await festivoService.desactivar(id);
  res.status(204).send();
});

module.exports = { listar, validar, desactivar };
