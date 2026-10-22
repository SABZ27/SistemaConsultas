// Correccion Ley Emiliani sobre los datos de Nager.Date.
//
// En Colombia los festivos eclesiasticos moviles (Ascension del Senor y Corpus
// Christi) se observean el lunes siguiente, no el dia de la plegaria: es la
// Ley Emiliani (Ley 51 de 1883,及其它 determinaciones del Ministerio del
// Interior). Nager.Date devuelve el dia de la plegaria, por ejemplo para 2026
// "Ascension Day" el 2026-05-14 (jueves) y "Corpus Christi" el 2026-06-04
// (jueves), cuando en el calendario oficial colombiano son el 2026-05-18 y el
// 2026-06-08 (lunes).
//
// Regla: SOLO para los nombres "Ascension Day" y "Corpus Christi"; si la fecha
// no cae en lunes se mueve al lunes siguiente antes de guardarse, actualizando
// tambien el anio cuando el traslado cruza el cambio de ano. Ningun otro
// festivo se toca (por ejemplo "Sacred Heart" ya lo publica el lunes).
const NOMBRES_MOVILES = ['Ascension Day', 'Corpus Christi'];

const DIAS_POR_SEMANA = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'];

// 0 = domingo ... 1 = lunes. Se calcula en UTC para no depender de la zona
// horaria del servidor.
function diaDeSemana(fecha) {
  return new Date(`${fecha}T00:00:00Z`).getUTCDay();
}

function esLunes(fecha) {
  return diaDeSemana(fecha) === 1;
}

function sumarDias(fecha, dias) {
  const fechaUtc = new Date(`${fecha}T00:00:00Z`);
  fechaUtc.setUTCDate(fechaUtc.getUTCDate() + dias);
  return fechaUtc.toISOString().slice(0, 10);
}

// Devuelve la fecha del lunes siguiente (si la fecha ya es lunes, la misma).
function siguienteLunes(fecha) {
  const dia = diaDeSemana(fecha);
  if (dia === 1) {
    return fecha;
  }
  const dias = dia === 0 ? 1 : 8 - dia;
  return sumarDias(fecha, dias);
}

// Normaliza un festivo de Nager.Date segun la Ley Emiliani.
// Devuelve { fecha, anio, desplazado } con la fecha final a guardar.
function ajustarLeyEmiliani({ fecha, nombre }) {
  const original = { fecha, anio: Number(String(fecha).slice(0, 4)), desplazado: false };

  if (!NOMBRES_MOVILES.includes(nombre)) {
    return original;
  }
  if (esLunes(fecha)) {
    return original;
  }

  const fechaFinal = siguienteLunes(fecha);
  return {
    fecha: fechaFinal,
    anio: Number(fechaFinal.slice(0, 4)),
    desplazado: true,
  };
}

module.exports = {
  NOMBRES_MOVILES,
  DIAS_POR_SEMANA,
  diaDeSemana,
  esLunes,
  siguienteLunes,
  ajustarLeyEmiliani,
};
