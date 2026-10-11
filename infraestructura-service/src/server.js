const crearApp = require('./app');
const env = require('./config/env');

const app = crearApp();

app.listen(env.port, () => {
  console.log(`infraestructura-service escuchando en el puerto ${env.port}`);
});
