const { NOMBRES_ES, nombreEnEspanol } = require('../src/utils/nombresFestivos');
const { FESTIVOS_CO_2026 } = require('./fixtures/nagerCo2026');

describe('mapa de nombres de festivos', () => {
  test('todas las claves del mapa existen en la respuesta de Nager.Date', () => {
    const nombresApi = FESTIVOS_CO_2026.map((festivo) => festivo.name);
    const claves = Object.keys(NOMBRES_ES);

    claves.forEach((clave) => {
      expect(nombresApi).toContain(clave);
    });
  });

  test('no hay claves huérfanas en el mapa', () => {
    const nombresApi = FESTIVOS_CO_2026.map((festivo) => festivo.name);
    const claves = Object.keys(NOMBRES_ES);

    expect(claves).toHaveLength(nombresApi.length);
  });

  test('todo festivo de la API tiene traducción al español', () => {
    FESTIVOS_CO_2026.forEach((festivo) => {
      expect(nombreEnEspanol(festivo.name)).toBeTruthy();
    });
  });

  test('los nombres corregidos de la API se traducen bien', () => {
    expect(nombreEnEspanol('Christmas Day')).toBe('Navidad');
    expect(nombreEnEspanol('Assumption of Mary')).toBe('La Asunción');
    expect(nombreEnEspanol('All Saints’ Day')).toBe('Día de los Santos');
    expect(nombreEnEspanol("New Year's Day")).toBe('Año Nuevo');
    expect(nombreEnEspanol("Saint Joseph's Day")).toBe('Día de San José');
    expect(nombreEnEspanol('Our Lady of Chiquinquirá Day')).toBe('Día de la Virgen de Chiquinquirá');
    expect(nombreEnEspanol('Battle of Boyacá')).toBe('Batalla de Boyacá');
  });

  test('un festivo desconocido devuelve null y el llamador usa el nombre de la API', () => {
    expect(nombreEnEspanol('Festival Inventado')).toBeNull();
    expect(nombreEnEspanol('')).toBeNull();
    expect(nombreEnEspanol(null)).toBeNull();
  });
});
