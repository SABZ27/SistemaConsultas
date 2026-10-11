const {
  NOMBRE_POR_DEFECTO,
  SUFIJO_OBLIGATORIO,
  nombreParaWorker,
  resolverConfigDePrueba,
  asegurarNombreDePrueba,
  aplicarEnvDePrueba,
} = require('./testEnv');

describe('configuración de la base de datos de pruebas', () => {
  test('aplicarEnvDePrueba es idempotente (mismo resultado al llamarla dos veces)', () => {
    const primera = aplicarEnvDePrueba();
    const segunda = aplicarEnvDePrueba();

    expect(segunda).toEqual(primera);
    expect(segunda.database).toBe(primera.database);
    expect(segunda.database.endsWith(SUFIJO_OBLIGATORIO)).toBe(true);
  });

  test('el nombre de pruebas es TEST_DB_NAME (o su default), no duplica el sufijo', () => {
    const config = aplicarEnvDePrueba();
    expect(config.database).toBe(process.env.TEST_DB_NAME || NOMBRE_POR_DEFECTO);
    expect(config.database).not.toBe(`${NOMBRE_POR_DEFECTO}${SUFIJO_OBLIGATORIO}`);
  });

  test('resolverConfigDePrueba es estable e idempotente', () => {
    expect(resolverConfigDePrueba()).toEqual(resolverConfigDePrueba());
  });

  test('cada worker obtiene una base distinta que sigue terminando en _test', () => {
    const base = process.env.TEST_DB_NAME || NOMBRE_POR_DEFECTO;
    const worker1 = resolverConfigDePrueba('1').database;
    const worker2 = resolverConfigDePrueba('2').database;

    expect(worker1).not.toBe(worker2);
    expect(worker1.endsWith(SUFIJO_OBLIGATORIO)).toBe(true);
    expect(worker2.endsWith(SUFIJO_OBLIGATORIO)).toBe(true);
    expect(nombreParaWorker(base, undefined)).toBe(base);
    expect(nombreParaWorker(base, '1')).toBe(nombreParaWorker(base, '1'));
  });

  test('asegurarNombreDePrueba rechaza nombres sin sufijo _test', () => {
    expect(() => asegurarNombreDePrueba('sistema_consultas_infra')).toThrow(/_test/);
    expect(() => asegurarNombreDePrueba(undefined)).toThrow(/_test/);
    expect(() => asegurarNombreDePrueba('mi_base_test')).not.toThrow();
  });
});
