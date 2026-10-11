const { Router } = require('express');

const recursoFisicoController = require('../controllers/recursoFisicoController');
const {
  autenticar,
  requiereInfraestructura,
  requiereInfraestructuraSiInactivos,
} = require('../middlewares/auth');
const { validar } = require('../middlewares/validar');
const { crearRecurso, actualizarRecurso } = require('../validators/recursoFisicoValidators');

const router = Router();

router.use(autenticar);

router.get('/', requiereInfraestructuraSiInactivos, recursoFisicoController.listar);
router.get('/:id', requiereInfraestructuraSiInactivos, recursoFisicoController.obtener);

router.post('/', requiereInfraestructura, validar(crearRecurso), recursoFisicoController.crear);
router.put(
  '/:id',
  requiereInfraestructura,
  validar(actualizarRecurso),
  recursoFisicoController.actualizar
);
router.delete('/:id', requiereInfraestructura, recursoFisicoController.desactivar);
router.patch('/:id/activar', requiereInfraestructura, recursoFisicoController.activar);

module.exports = router;
