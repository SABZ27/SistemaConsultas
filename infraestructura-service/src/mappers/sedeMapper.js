function aRespuesta(fila) {
  return {
    id: fila.id,
    nombre: fila.nombre,
    tipoEstructura: fila.tipo_estructura,
    estado: Boolean(fila.estado),
  };
}

module.exports = { aRespuesta };
