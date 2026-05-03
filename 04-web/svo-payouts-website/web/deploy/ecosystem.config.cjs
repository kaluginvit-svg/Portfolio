/**
 * PM2: запуск после деплоя standalone-сборки.
 * На сервере в каталоге с `server.js` и `ecosystem.config.cjs`:
 *   pm2 start ecosystem.config.cjs
 *   pm2 save && pm2 startup
 */
module.exports = {
  apps: [
    {
      name: "svo-landing",
      script: "server.js",
      instances: 1,
      autorestart: true,
      max_memory_restart: "450M",
      env: {
        NODE_ENV: "production",
        PORT: "3000",
        HOSTNAME: "0.0.0.0",
      },
    },
  ],
};
