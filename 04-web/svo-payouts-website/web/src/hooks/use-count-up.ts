"use client";

import { useEffect, useState } from "react";

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Плавный подсчёт до `end` за `durationMs` (с учётом prefers-reduced-motion). */
export function useCountUp(end: number, durationMs = 1100): number {
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!Number.isFinite(end) || end <= 0) {
      setValue(end);
      return;
    }
    if (prefersReducedMotion()) {
      setValue(end);
      return;
    }

    setValue(0);
    const start = performance.now();
    let frame: number;

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - (1 - t) ** 3;
      setValue(end * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [end, durationMs]);

  return value;
}
