// Reduce un texto a un detalle breve y sin datos personales para la bitacora
// consultas_servicio_externo. Se eliminan correos electronicos y cadenas que
// parezcan un correo, y se trunca al maximo indicado.
const CORREO = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi;
const ESPACIOS = /\s+/g;

function detalleBreve(texto, maximo = 255) {
  if (texto === null || texto === undefined || texto === '') {
    return null;
  }
  const limpio = String(texto)
    .replace(CORREO, '[correo]')
    .replace(ESPACIOS, ' ')
    .trim();
  if (!limpio) {
    return null;
  }
  return limpio.length > maximo ? limpio.slice(0, maximo) : limpio;
}

module.exports = { detalleBreve };
