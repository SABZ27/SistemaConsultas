const correoService = require('../services/correoService');
const asyncHandler = require('../utils/asyncHandler');

const enviar = asyncHandler(async (req, res) => {
  res.status(201).json(await correoService.enviar(req.datos));
});

module.exports = { enviar };
