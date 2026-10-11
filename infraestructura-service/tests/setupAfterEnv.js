const { asegurarBaseDePrueba } = require('./bootstrap');

// setupFilesAfterEnv: se ejecuta en el worker antes de los tests del archivo.
// Garantiza que la base del worker exista con el esquema aplicado.
beforeAll(async () => {
  await asegurarBaseDePrueba();
});
