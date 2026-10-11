const zonaService = require('../services/zonaService');
const recursoFisicoService = require('../services/recursoFisicoService');
const asyncHandler = require('../utils/asyncHandler');
const { incluirInactivos, numeroQuery } = require('../utils/query');

const sedeIdQuery = (req) => numeroQuery(req.query.sedeId ?? req.query.sede_id);

const listar = asyncHandler(async (req, res) => {
  res.json(
    await zonaService.listar({ sedeId: sedeIdQuery(req), incluirInactivos: incluirInactivos(req) })
  );
});

const obtener = asyncHandler(async (req, res) => {
  res.json(await zonaService.obtener(Number(req.params.id), { incluirInactivos: incluirInactivos(req) }));
});

const crear = asyncHandler(async (req, res) => {
  res.status(201).json(await zonaService.crear(req.datos));
});

const actualizar = asyncHandler(async (req, res) => {
  res.json(await zonaService.actualizar(Number(req.params.id), req.datos));
});

const desactivar = asyncHandler(async (req, res) => {
  await zonaService.desactivar(Number(req.params.id));
  res.status(204).send();
});

const activar = asyncHandler(async (req, res) => {
  res.json(await zonaService.activar(Number(req.params.id)));
});

const listarRecursos = asyncHandler(async (req, res) => {
  res.json(
    await recursoFisicoService.listarPorZona(Number(req.params.id), {
      incluirInactivos: incluirInactivos(req),
    })
  );
});

module.exports = {
  listar,
  obtener,
  crear,
  actualizar,
  desactivar,
  activar,
  listarRecursos,
};
