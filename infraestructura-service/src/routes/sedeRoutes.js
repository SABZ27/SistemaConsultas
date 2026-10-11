const { Router } = require('express');

const sedeController = require('../controllers/sedeController');
const {
  autenticar,
  requiereInfraestructura,
  requiereInfraestructuraSiInactivos,
} = require('../middlewares/auth');
const { validar } = require('../middlewares/validar');
const { crearSede, actualizarSede } = require('../validators/sedeValidators');

const router = Router();

router.use(autenticar);

router.get('/', requiereInfraestructuraSiInactivos, sedeController.listar);
router.get('/:id', requiereInfraestructuraSiInactivos, sedeController.obtener);
router.get('/:id/zonas', sedeController.listarZonas);
router.get('/:id/recursos-fisicos', sedeController.listarRecursos);
router.get('/:id/estructura', sedeController.estructura);

router.post('/', requiereInfraestructura, validar(crearSede), sedeController.crear);
router.put('/:id', requiereInfraestructura, validar(actualizarSede), sedeController.actualizar);
router.delete('/:id', requiereInfraestructura, sedeController.desactivar);
router.patch('/:id/activar', requiereInfraestructura, sedeController.activar);

module.exports = router;
