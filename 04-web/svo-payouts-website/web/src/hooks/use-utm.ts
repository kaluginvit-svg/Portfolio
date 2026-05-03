"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

const UTM_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
] as const;

export function useUtmParams(): Record<string, string> {
  const searchParams = useSearchParams();

  return useMemo(() => {
    const out: Record<string, string> = {};
    for (const key of UTM_KEYS) {
      const v = searchParams.get(key);
      if (v) out[key] = v;
    }
    return out;
  }, [searchParams]);
}
