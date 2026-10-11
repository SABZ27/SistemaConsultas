const { z } = require('zod');

const idPositivo = z.coerce
  .number({ invalid_type_error: 'El sedeId debe ser un número.' })
  .int('El sedeId debe ser un número entero.')
  .positive('El sedeId debe ser un número positivo.');

const nombre = z
  .string({
    required_error: 'El nombre es obligatorio',
    invalid_type_error: 'El nombre debe ser un texto',
  })
  .min(1, 'El nombre no puede estar vacío')
  .max(100, 'El nombre no puede superar los 100 caracteres');

const crearZona = z
  .object({
    sedeId: idPositivo,
    nombre,
  })
  .strict();

const actualizarZona = z
  .object({
    nombre,
  })
  .strict();

module.exports = { crearZona, actualizarZona };
