const { z } = require('zod');

const TIPOS_ESTRUCTURA = ['BLOQUES', 'SALONES', 'PISOS'];

const nombre = z
  .string({
    required_error: 'El nombre es obligatorio',
    invalid_type_error: 'El nombre debe ser un texto',
  })
  .min(3, 'El nombre debe tener al menos 3 caracteres')
  .max(100, 'El nombre no puede superar los 100 caracteres');

const tipoEstructura = z.enum(TIPOS_ESTRUCTURA, {
  errorMap: () => ({
    message: 'El tipo de estructura no es un valor válido. Valores permitidos: BLOQUES, SALONES, PISOS',
  }),
});

const crearSede = z
  .object({
    nombre,
    tipoEstructura,
  })
  .strict();

const actualizarSede = z
  .object({
    nombre,
    tipoEstructura,
  })
  .strict();

module.exports = { TIPOS_ESTRUCTURA, crearSede, actualizarSede };
