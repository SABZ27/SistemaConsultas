const { z } = require('zod');

const enviarCorreo = z
  .object({
    para: z
      .string({ required_error: 'El destinatario es obligatorio' })
      .email('El destinatario no tiene un formato válido')
      .max(150, 'El destinatario no puede superar los 150 caracteres'),
    paraNombre: z.string().max(100, 'El nombre no puede superar los 100 caracteres').optional(),
    asunto: z
      .string({ required_error: 'El asunto es obligatorio' })
      .min(1, 'El asunto es obligatorio')
      .max(200, 'El asunto no puede superar los 200 caracteres'),
    contenido: z
      .string({ required_error: 'El contenido es obligatorio' })
      .min(1, 'El contenido es obligatorio')
      .max(20000, 'El contenido no puede superar los 20000 caracteres'),
  })
  .strict();

module.exports = { enviarCorreo };
