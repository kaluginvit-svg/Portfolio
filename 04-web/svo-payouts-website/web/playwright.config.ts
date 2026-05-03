import { defineConfig, devices } from "@playwright/test";

/** Отдельный порт, чтобы не конфликтовать с `npm run dev` на :3000. */
const e2ePort = process.env.PW_TEST_PORT ?? "4173";
const defaultBase = `http://127.0.0.1:${e2ePort}`;
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? defaultBase;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["list"]],
  timeout: 60_000,
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `npm run build && npx next start -H 127.0.0.1 -p ${e2ePort}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
