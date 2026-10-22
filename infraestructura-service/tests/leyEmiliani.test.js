const { ajustarLeyEmiliani, esLunes, siguienteLunes } = require('../src/utils/leyEmiliani');

describe('corrección Ley Emiliani', () => {
  test('la Ascensión se mueve al lunes siguiente', () => {
    const resultado = ajustarLeyEmiliani({ fecha: '2026-05-14', nombre: 'Ascension Day' });
    expect(resultado.fecha).toBe('2026-05-18');
    expect(resultado.anio).toBe(2026);
    expect(resultado.desplazado).toBe(true);
  });

  test('Corpus Christi se mueve al lunes siguiente', () => {
    const resultado = ajustarLeyEmiliani({ fecha: '2026-06-04', nombre: 'Corpus Christi' });
    expect(resultado.fecha).toBe('2026-06-08');
    expect(resultado.anio).toBe(2026);
    expect(resultado.desplazado).toBe(true);
  });

  test('un festivo que ya es lunes no se mueve', () => {
    const resultado = ajustarLeyEmiliani({ fecha: '2026-06-15', nombre: 'Sacred Heart' });
    expect(resultado.fecha).toBe('2026-06-15');
    expect(resultado.anio).toBe(2026);
    expect(resultado.desplazado).toBe(false);
  });

  test('los demás festivos no se tocan', () => {
    const resultado = ajustarLeyEmiliani({ fecha: '2026-12-25', nombre: 'Christmas Day' });
    expect(resultado.fecha).toBe('2026-12-25');
    expect(resultado.desplazado).toBe(false);
  });

  test('el año se actualiza cuando el traslado cruza el cambio de año', () => {
    const resultado = ajustarLeyEmiliani({ fecha: '2026-12-31', nombre: 'Ascension Day' });
    expect(resultado.fecha).toBe('2027-01-04');
    expect(resultado.anio).toBe(2027);
  });

  test('siguiente lunes a partir de cada día de la semana', () => {
    expect(siguienteLunes('2026-05-14')).toBe('2026-05-18'); // jueves
    expect(siguienteLunes('2026-05-15')).toBe('2026-05-18'); // viernes
    expect(siguienteLunes('2026-05-16')).toBe('2026-05-18'); // sábado
    expect(siguienteLunes('2026-05-17')).toBe('2026-05-18'); // domingo
    expect(siguienteLunes('2026-05-18')).toBe('2026-05-18'); // lunes
    expect(siguienteLunes('2026-05-19')).toBe('2026-05-25'); // martes
  });

  test('esLunes reconoce solo el lunes', () => {
    expect(esLunes('2026-06-15')).toBe(true);
    expect(esLunes('2026-06-14')).toBe(false);
    expect(esLunes('2026-06-20')).toBe(false);
  });
});
