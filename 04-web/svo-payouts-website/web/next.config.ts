import type { NextConfig } from "next";

const envDevOrigins =
  process.env.NEXT_ALLOWED_DEV_ORIGINS?.split(/[\s,]+/).map((s) => s.trim()).filter(Boolean) ?? [];

const nextConfig: NextConfig = {
  /** Docker / Node: каталог `.next/standalone` + `node server.js` (см. web/README.md — деплой). */
  output: "standalone",

  compiler: {
    removeConsole:
      process.env.NODE_ENV === "production"
        ? { exclude: ["error", "warn"] }
        : false,
  },

  experimental: {
    optimizePackageImports: ["lucide-react"],
  },

  /**
   * Открываете dev по IP в LAN (телефон / другой ПК)? Без этого Next.js отклоняет Origin
   * для `/_next/*` и HMR-WebSocket — чанки не грузятся, «белый экран» / падение в браузере.
   * Шаблоны как в доке: https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins
   * В production не применяется.
   */
  allowedDevOrigins: [
    "*.local",
    "127.0.0.1",
    "192.168.*.*",
    "10.*.*.*",
    "172.*.*.*",
    ...envDevOrigins,
  ],
};

export default nextConfig;
