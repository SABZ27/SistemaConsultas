const { Router } = require('express');

const correoController = require('../controllers/correoController');
const { autenticar } = require('../middlewares/auth');
const { validar } = require('../middlewares/validar');
const { enviarCorreo } = require('../validators/correoValidators');

const router = Router();

router.use(autenticar);

// Cualquier usuario autenticado puede pedir el envio de un correo.
router.post('/', validar(enviarCorreo), correoController.enviar);

module.exports = router;
