const { Router } = require('express');

const correoController = require('../controllers/correoController');
const { autenticar, requiereRol } = require('../middlewares/auth');
const { validar } = require('../middlewares/validar');
const { enviarCorreo } = require('../validators/correoValidators');

const router = Router();

router.use(autenticar);

// Cambio Fase 3: el envio de correo es una operacion de servicio a servicio.
// Solo un token con rol 'SERVICIO' (el que firma el backend FastAPI con el
// token interno) puede enviar correos; cualquier token de usuario responde
// 403, aunque este autenticado.
router.post('/', requiereRol('SERVICIO'), validar(enviarCorreo), correoController.enviar);

module.exports = router;
