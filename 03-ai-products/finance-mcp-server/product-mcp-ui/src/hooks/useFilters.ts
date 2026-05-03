"use client";

import { useCallback, useMemo, useState } from "react";

export function useRecordFilters<T extends Record<string, string>>(initial: T) {
  const [filters, setFilters] = useState<T>(initial);
  const set = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setFilters((f) => ({ ...f, [key]: value }));
  }, []);
  const reset = useCallback(() => setFilters(initial), [initial]);
  const payload = useMemo(() => {
    const out: Record<string, string> = {};
    (Object.keys(filters) as (keyof T)[]).forEach((k) => {
      const v = filters[k];
      if (v !== undefined && String(v).trim() !== "") {
        out[String(k)] = String(v);
      }
    });
    return out;
  }, [filters]);
  return { filters, set, reset, payload };
}
