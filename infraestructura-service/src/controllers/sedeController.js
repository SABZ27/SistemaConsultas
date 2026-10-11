const sedeService = require('../services/sedeService');
const zonaService = require('../services/zonaService');
const recursoFisicoService = require('../services/recursoFisicoService');
const estructuraService = require('../services/estructuraService');
const asyncHandler = require('../utils/asyncHandler');
const { incluirInactivos } = require('../utils/query');

const listar = asyncHandler(async (req, res) => {
  res.json(await sedeService.listar({ incluirInactivos: incluirInactivos(req) }));
});

const obtener = asyncHandler(async (req, res) => {
  res.json(await sedeService.obtener(Number(req.params.id), { incluirInactivos: incluirInactivos(req) }));
});

const crear = asyncHandler(async (req, res) => {
  res.status(201).json(await sedeService.crear(req.datos));
});

const actualizar = asyncHandler(async (req, res) => {
  res.json(await sedeService.actualizar(Number(req.params.id), req.datos));
});

const desactivar = asyncHandler(async (req, res) => {
  await sedeService.desactivar(Number(req.params.id));
  res.status(204).send();
});

const activar = asyncHandler(async (req, res) => {
  res.json(await sedeService.activar(Number(req.params.id)));
});

const listarZonas = asyncHandler(async (req, res) => {
  res.json(
    await zonaService.listarPorSede(Number(req.params.id), { incluirInactivos: incluirInactivos(req) })
  );
});

const listarRecursos = asyncHandler(async (req, res) => {
  res.json(
    await recursoFisicoService.listarPorSede(Number(req.params.id), {
      incluirInactivos: incluirInactivos(req),
    })
  );
});

const estructura = asyncHandler(async (req, res) => {
  res.json(await estructuraService.obtenerEstructura(Number(req.params.id)));
});

module.exports = {
  listar,
  obtener,
  crear,
  actualizar,
  desactivar,
  activar,
  listarZonas,
  listarRecursos,
  estructura,
};
