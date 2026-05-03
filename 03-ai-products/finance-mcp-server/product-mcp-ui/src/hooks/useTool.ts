"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { clientCallTool } from "@/lib/mcp-client";
import type { ToolExecutionResponse } from "@/types/api";

export function useToolMutation<T = unknown>() {
  return useMutation({
    mutationFn: async ({ tool, payload }: { tool: string; payload?: Record<string, unknown> }): Promise<ToolExecutionResponse<T>> => {
      return clientCallTool<T>(tool, payload ?? {});
    },
  });
}

export function useToolQuery<T = unknown>(tool: string, payload: Record<string, unknown>, enabled = true) {
  return useQuery({
    queryKey: ["tool", tool, payload],
    queryFn: () => clientCallTool<T>(tool, payload),
    enabled,
  });
}
