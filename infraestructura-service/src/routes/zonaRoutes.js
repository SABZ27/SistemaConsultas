const { Router } = require('express');

const zonaController = require('../controllers/zonaController');
const {
  autenticar,
  requiereInfraestructura,
  requiereInfraestructuraSiInactivos,
} = require('../middlewares/auth');
const { validar } = require('../middlewares/validar');
const { crearZona, actualizarZona } = require('../validators/zonaValidators');

const router = Router();

router.use(autenticar);

router.get('/', requiereInfraestructuraSiInactivos, zonaController.listar);
router.get('/:id', requiereInfraestructuraSiInactivos, zonaController.obtener);
router.get('/:id/recursos-fisicos', zonaController.listarRecursos);

router.post('/', requiereInfraestructura, validar(crearZona), zonaController.crear);
router.put('/:id', requiereInfraestructura, validar(actualizarZona), zonaController.actualizar);
router.delete('/:id', requiereInfraestructura, zonaController.desactivar);
router.patch('/:id/activar', requiereInfraestructura, zonaController.activar);

module.exports = router;
