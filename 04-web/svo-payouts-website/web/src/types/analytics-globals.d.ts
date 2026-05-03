export {};

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    ym?: (counterId: number | string, method: string, ...args: unknown[]) => void;
    /** Задаётся в layout при рантайм-ID Метрики (YM_COUNTER_ID на сервере). */
    __SVO_YM_ID?: string;
  }
}
