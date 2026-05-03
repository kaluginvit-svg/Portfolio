/**
 * ID счётчиков для серверного рендера: без префикса NEXT_PUBLIC_ — не подменяются при `next build`,
 * подхватываются из `env_file` Docker / `.env` на VPS без пересборки образа.
 * Дублируйте значения из NEXT_PUBLIC_* или задавайте только эти имена на сервере.
 */
function stripEnv(s: string | undefined): string {
  return (s ?? "").replace(/\r/g, "").trim();
}

export function runtimeYmCounterId(): string {
  const direct = stripEnv(process.env.YM_COUNTER_ID);
  if (direct) return direct;
  return stripEnv(process.env.NEXT_PUBLIC_YM_ID);
}

export function runtimeGaMeasurementId(): string {
  const direct = stripEnv(process.env.GA_MEASUREMENT_ID);
  if (direct) return direct;
  return stripEnv(process.env.NEXT_PUBLIC_GA_ID);
}
