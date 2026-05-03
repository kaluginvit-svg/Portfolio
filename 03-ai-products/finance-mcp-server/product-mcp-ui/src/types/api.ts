export type ToolExecutionResponse<T = unknown> = {
  ok: boolean;
  tool: string;
  payload: Record<string, unknown>;
  success?: boolean;
  result?: T;
  error?: string;
  mock?: boolean;
  technical?: string;
};

export type ReportExportResponse = {
  path: string | null;
  report_type: string;
  error?: string | null;
};
