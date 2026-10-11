const { z } = require('zod');

const TIPOS_RECURSO = ['SALON', 'LABORATORIO', 'AUDITORIO', 'SALA', 'OFICINA'];

const enteroPositivo = (campo) =>
  z.coerce
    .number({ invalid_type_error: `El ${campo} debe ser un número.` })
    .int(`El ${campo} debe ser un número entero.`)
    .positive(`El ${campo} debe ser un número positivo.`);

const nombre = z
  .string({
    required_error: 'El nombre es obligatorio',
    invalid_type_error: 'El nombre debe ser un texto',
  })
  .min(1, 'El nombre no puede estar vacío')
  .max(100, 'El nombre no puede superar los 100 caracteres');

const tipo = z.enum(TIPOS_RECURSO, {
  errorMap: () => ({
    message:
      'El tipo no es un valor válido. Valores permitidos: SALON, LABORATORIO, AUDITORIO, SALA, OFICINA',
  }),
});

const crearRecurso = z
  .object({
    sedeId: enteroPositivo('sedeId'),
    zonaId: enteroPositivo('zonaId').nullable().optional(),
    nombre,
    tipo: tipo.optional(),
  })
  .strict();

const actualizarRecurso = z
  .object({
    nombre,
    tipo: tipo.optional(),
    zonaId: enteroPositivo('zonaId').nullable().optional(),
  })
  .strict();

module.exports = { TIPOS_RECURSO, crearRecurso, actualizarRecurso };
