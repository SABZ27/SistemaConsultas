const { Router } = require('express');

const festivoController = require('../controllers/festivoController');
const { autenticar, requiereRol } = require('../middlewares/auth');
const { validar } = require('../middlewares/validar');
const { validarFecha, validarAnio } = require('../validators/festivoValidators');

const router = Router();

router.use(autenticar);

router.get('/validar', validar(validarFecha, 'query'), festivoController.validar);
router.get('/', validar(validarAnio, 'query'), festivoController.listar);

// Borrado logico del festivo (estado = 0). Solo ADMINISTRADOR.
router.delete('/:id', requiereRol('ADMINISTRADOR'), festivoController.desactivar);

module.exports = router;
