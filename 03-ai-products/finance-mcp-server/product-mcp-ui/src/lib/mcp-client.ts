/**
 * Browser-safe client: calls Next.js API routes only.
 */

import type { ToolExecutionResponse } from "@/types/api";

export async function clientCallTool<T = unknown>(
  tool: string,
  payload: Record<string, unknown> = {}
): Promise<ToolExecutionResponse<T>> {
  const res = await fetch("/api/tools", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, payload }),
  });
  const json = (await res.json()) as ToolExecutionResponse<T>;
  return json;
}

export async function clientUpload(formData: FormData): Promise<{
  ok: boolean;
  result?: unknown;
  error?: string;
  debug?: string;
}> {
  const res = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });
  const json = await res.json();
  return json;
}
