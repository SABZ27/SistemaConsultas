const servicioExternoRepository = require('../repositories/servicioExternoRepository');
const { AppError } = require('../utils/errores');

const NOMBRE_NAGER = 'Nager.Date';
const NOMBRE_BREVO = 'Brevo';

// Los proveedores se buscan por nombre (clave logica). Si no estan sembrados
// el servicio responde 503: no se inventa un id de servicio nulo.
async function obtenerActivo(nombre) {
  const fila = await servicioExternoRepository.buscarActivoPorNombre(nombre);
  if (!fila) {
    throw new AppError(503, `El proveedor externo "${nombre}" no está configurado.`);
  }
  return {
    id: fila.id,
    nombre: fila.nombre,
    url_base: fila.url_base,
    descripcion: fila.descripcion,
  };
}

async function listar() {
  return servicioExternoRepository.listarActivos();
}

module.exports = { obtenerActivo, listar, NOMBRE_NAGER, NOMBRE_BREVO };
