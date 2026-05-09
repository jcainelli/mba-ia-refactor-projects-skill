const express = require('express');
const { settings } = require('./config/settings');
const { initDb } = require('./config/database');
const checkoutRoutes = require('./views/checkoutRoutes');
const reportRoutes = require('./views/reportRoutes');
const userRoutes = require('./views/userRoutes');
const { errorHandler } = require('./middlewares/errorHandler');

async function bootstrap() {
  await initDb();

  const app = express();
  app.use(express.json());

  app.use('/api/checkout', checkoutRoutes);
  app.use('/api/admin', reportRoutes);
  app.use('/api/users', userRoutes);

  app.use(errorHandler);

  app.listen(settings.port, () => {
    console.log(`LMS API running on port ${settings.port}`);
  });
}

bootstrap().catch((err) => {
  console.error('Bootstrap failure:', err);
  process.exit(1);
});
