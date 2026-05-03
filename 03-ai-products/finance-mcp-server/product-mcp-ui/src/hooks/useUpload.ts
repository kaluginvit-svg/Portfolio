"use client";

import { useMutation } from "@tanstack/react-query";

export function useUploadMutation() {
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      return res.json() as Promise<{
        ok: boolean;
        result?: unknown;
        error?: string;
        preview?: string[][];
        conversionNote?: string;
        warnings?: string[];
      }>;
    },
  });
}
