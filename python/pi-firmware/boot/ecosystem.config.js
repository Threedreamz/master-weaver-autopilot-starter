module.exports = {
  apps: [
    {
      name: "camera",
      script: "dist/server.js",
      cwd: "/opt/autopilot/python/pi-firmware",
      env: { PORT: 4801, NODE_ENV: "production" },
      restart_delay: 3000,
      max_restarts: 10,
    },
    {
      name: "ipad-app",
      script: "server.js",
      cwd: "/opt/autopilot/apps/ipad/.next/standalone",
      env: { PORT: 4800, HOSTNAME: "0.0.0.0", NODE_ENV: "production" },
      restart_delay: 3000,
    },
    {
      name: "setup-portal",
      script: "server.js",
      cwd: "/opt/autopilot/apps/setup/.next/standalone",
      env: { PORT: 4804, HOSTNAME: "0.0.0.0", NODE_ENV: "production" },
      restart_delay: 3000,
    },
  ],
};
