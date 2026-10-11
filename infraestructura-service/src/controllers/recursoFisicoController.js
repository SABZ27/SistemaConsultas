const recursoFisicoService = require('../services/recursoFisicoService');
const asyncHandler = require('../utils/asyncHandler');
const { incluirInactivos, numeroQuery } = require('../utils/query');

const listar = asyncHandler(async (req, res) => {
  res.json(
    await recursoFisicoService.listar({
      sedeId: numeroQuery(req.query.sedeId ?? req.query.sede_id),
      zonaId: numeroQuery(req.query.zonaId ?? req.query.zona_id),
      incluirInactivos: incluirInactivos(req),
    })
  );
});

const obtener = asyncHandler(async (req, res) => {
  res.json(
    await recursoFisicoService.obtener(Number(req.params.id), {
      incluirInactivos: incluirInactivos(req),
    })
  );
});

const crear = asyncHandler(async (req, res) => {
  res.status(201).json(await recursoFisicoService.crear(req.datos));
});

const actualizar = asyncHandler(async (req, res) => {
  res.json(await recursoFisicoService.actualizar(Number(req.params.id), req.datos));
});

const desactivar = asyncHandler(async (req, res) => {
  await recursoFisicoService.desactivar(Number(req.params.id));
  res.status(204).send();
});

const activar = asyncHandler(async (req, res) => {
  res.json(await recursoFisicoService.activar(Number(req.params.id)));
});

module.exports = { listar, obtener, crear, actualizar, desactivar, activar };
