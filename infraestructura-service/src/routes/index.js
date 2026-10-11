const { Router } = require('express');

const router = Router();

router.use('/sedes', require('./sedeRoutes'));
router.use('/zonas', require('./zonaRoutes'));
router.use('/recursos-fisicos', require('./recursoFisicoRoutes'));

module.exports = router;
