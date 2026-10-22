const { Router } = require('express');

const serviciosExternosController = require('../controllers/serviciosExternosController');
const { autenticar } = require('../middlewares/auth');

const router = Router();

router.use(autenticar);

// Listado de los proveedores externos configurados (solo los activos).
router.get('/', serviciosExternosController.listar);

module.exports = router;
