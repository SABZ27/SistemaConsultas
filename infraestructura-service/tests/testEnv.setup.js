// setupFiles: se ejecuta antes de cargar cada archivo de test y antes de que la
// app cree su pool. Ajusta DB_* para que apunte a la base del worker actual.
require('./testEnv').aplicarEnvDePrueba(process.env.JEST_WORKER_ID);
