function aRespuesta(fila) {
  return {
    id: fila.id,
    nombre: fila.nombre,
    sedeId: fila.sede_id,
    sedeNombre: fila.sede_nombre,
    estado: Boolean(fila.estado),
  };
}

function aRespuestaConRecursos(fila, recursos) {
  return {
    ...aRespuesta(fila),
    recursos,
  };
}

module.exports = { aRespuesta, aRespuestaConRecursos };
