module.exports = {
  apps: [
    {
      name: "autosecure-api",
      cwd: "/root/autosecure",
      script: ".venv/bin/python",
      args: "-m uvicorn app:app --host 127.0.0.1 --port 8000 --app-dir web",
      env: {
        CORS_ORIGINS: "http://127.0.0.1:3000,http://localhost:3000",
      },
      autorestart: true,
      max_restarts: 10,
      watch: false,
      max_memory_size: "512M",
    },
    {
      name: "autosecure-web",
      cwd: "/root/autosecure",
      script: "node",
      args: "web/.output/server/index.mjs",
      env: {
        NITRO_HOST: "0.0.0.0",
        HOST: "0.0.0.0",
        PORT: "3000",
        NITRO_PORT: "3000",
      },
      autorestart: true,
      max_restarts: 10,
      watch: false,
      max_memory_size: "512M",
    },
    {
      name: "autosecure-bot",
      cwd: "/root/autosecure",
      script: ".venv/bin/python",
      args: "-u bot.py",
      env: {
        PYTHONUNBUFFERED: "1",
      },
      autorestart: true,
      max_restarts: 10,
      watch: false,
      max_memory_size: "512M",
    },
  ],
};
