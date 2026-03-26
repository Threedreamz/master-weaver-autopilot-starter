module.exports = {
  apps: [
    // Camera server runs on Kamera-Pi (autopilot-cam.local:4811), not here
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
