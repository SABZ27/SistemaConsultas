const { z } = require('zod');

const FECHA = /^\d{4}-\d{2}-\d{2}$/;

// Valida el formato y que la fecha exista en el calendario (2026-02-30 no).
function esFechaValida(valor) {
  if (!FECHA.test(valor)) {
    return false;
  }
  const [anio, mes, dia] = valor.split('-').map(Number);
  const fecha = new Date(Date.UTC(anio, mes - 1, dia));
  return (
    fecha.getUTCFullYear() === anio && fecha.getUTCMonth() === mes - 1 && fecha.getUTCDate() === dia
  );
}

const validarFecha = z.object({
  fecha: z
    .string({ required_error: 'La fecha es obligatoria' })
    .refine(esFechaValida, 'La fecha debe ser una fecha válida con formato YYYY-MM-DD'),
  pais: z.string().length(2, 'El código de país debe tener 2 letras').optional(),
});

const validarAnio = z.object({
  anio: z.coerce
    .number({ invalid_type_error: 'El año debe ser un número' })
    .int('El año debe ser un número entero')
    .min(1970, 'El año debe ser mayor a 1970')
    .max(2100, 'El año no puede superar 2100'),
  pais: z.string().length(2, 'El código de país debe tener 2 letras').optional(),
});

module.exports = { validarFecha, validarAnio, esFechaValida };
