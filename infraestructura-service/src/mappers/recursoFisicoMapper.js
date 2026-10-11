function calcularUbicacion(fila) {
  return [fila.sede_nombre, fila.zona_nombre, fila.nombre].filter(Boolean).join(' · ');
}

function aRespuesta(fila) {
  return {
    id: fila.id,
    nombre: fila.nombre,
    tipo: fila.tipo,
    estado: Boolean(fila.estado),
    sedeId: fila.sede_id,
    sedeNombre: fila.sede_nombre,
    zonaId: fila.zona_id ?? null,
    zonaNombre: fila.zona_nombre ?? null,
    ubicacion: calcularUbicacion(fila),
  };
}

module.exports = { aRespuesta, calcularUbicacion };
