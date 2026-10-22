const { Router } = require('express');

const router = Router();

router.use('/festivos', require('./festivoRoutes'));
router.use('/correos', require('./correoRoutes'));
router.use('/servicios-externos', require('./serviciosExternosRoutes'));

module.exports = router;
