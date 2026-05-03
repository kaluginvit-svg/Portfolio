/**
 * Server-only: invoke product-mcp tools via Python subprocess or optional HTTP bridge.
 */

import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";

const execFileAsync = promisify(execFile);

export type McpDispatchResult<T = unknown> =
  | { success: true; result: T }
  | { success: false; error: string; data?: Record<string, unknown> };

function mockDispatch<T = unknown>(tool: string, payload: Record<string, unknown>): McpDispatchResult<T> {
  switch (tool) {
    case "health_check":
      return {
        success: true,
        result: {
          server_status: "mock",
          db_path: "(mock — set PRODUCT_MCP_PATH)",
          available_tools: ["health_check", "list_companies", "calculate_kpis"],
          counts_by_table: { companies: 0, alerts: 0, financial_records: 0 },
        } as T,
      };
    case "list_companies":
      return {
        success: true,
        result: { companies: [{ id: 1, name: "Demo Corp (mock)", currency: "EUR", created_at: "" }] } as T,
      };
    case "list_financial_records":
      return { success: true, result: { records: [] } as T };
    case "list_budget_records":
      return { success: true, result: { records: [] } as T };
    case "list_cash_positions":
      return { success: true, result: { records: [] } as T };
    case "list_contracts":
      return { success: true, result: { records: [] } as T };
    case "list_investment_projects":
      return { success: true, result: { records: [] } as T };
    case "calculate_kpis":
      return {
        success: true,
        result: {
          total_revenue: 0,
          total_opex: 0,
          gross_profit: 0,
          ebitda: 0,
          ebitda_margin: null,
          net_cash_flow: 0,
          accounts_receivable_total: 0,
          accounts_payable_total: 0,
          cash_balance: 0,
          error: "Mock data — connect product-mcp",
        } as T,
      };
    case "plan_vs_fact":
      return {
        success: true,
        result: {
          total_plan: 0,
          total_fact: 0,
          variance_abs: 0,
          variance_pct: null,
          breakdown_by_category: [],
        } as T,
      };
    case "liquidity_forecast":
      return {
        success: true,
        result: {
          opening_cash: 0,
          projected_inflows: 0,
          projected_outflows: 0,
          ending_cash: 0,
          daily_projection: [],
          risk_flags: ["mock_mode"],
        } as T,
      };
    case "payment_calendar":
      return { success: true, result: { records: [] } as T };
    case "contract_risk_scan":
      return {
        success: true,
        result: {
          expiring_soon: [],
          missing_payment_terms: [],
          missing_penalty_terms: [],
          missing_amount: [],
          no_end_date: [],
          penalty_detected: [],
          alerts_created: 0,
        } as T,
      };
    case "evaluate_investment":
      return {
        success: true,
        result: {
          project_id: Number(payload.project_id) || 0,
          npv: null,
          irr: null,
          payback_period: null,
          profitability_index: null,
          recommendation: "Mock — connect backend",
        } as T,
      };
    case "import_csv":
      return { success: true, result: { imported_count: 0, rejected_count: 0, errors: ["mock mode"] } as T };
    case "import_contract":
      return { success: true, result: { contract_id: null, parsed: {}, warnings: ["mock mode"] } as T };
    case "export_report":
      return { success: true, result: { path: "", report_type: String(payload.report_type || ""), error: "mock" } as T };
    case "find_records":
      return { success: true, result: { records: [] } as T };
    default:
      return {
        success: false,
        error: `Unknown tool or mock not defined: ${tool}`,
        data: {},
      };
  }
}

async function invokeHttp(tool: string, payload: Record<string, unknown>): Promise<McpDispatchResult> {
  const base = process.env.MCP_BASE_URL!.replace(/\/$/, "");
  const res = await fetch(`${base}/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, payload }),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    return { success: false, error: `HTTP ${res.status}: ${text}`, data: {} };
  }
  return (await res.json()) as McpDispatchResult;
}

async function invokePython(tool: string, payload: Record<string, unknown>): Promise<McpDispatchResult> {
  const root = process.env.PRODUCT_MCP_PATH?.trim();
  if (!root || !fs.existsSync(path.join(root, "registry.py"))) {
    return mockDispatch(tool, payload);
  }

  const python = process.env.MCP_PYTHON || "python";
  const script = path.join(process.cwd(), "scripts", "mcp_invoke.py");
  if (!fs.existsSync(script)) {
    return { success: false, error: `Missing script: ${script}`, data: {} };
  }

  const env = {
    ...process.env,
    PRODUCT_MCP_PATH: path.resolve(root),
    PYTHONUTF8: "1",
  };

  try {
    const { stdout, stderr } = await execFileAsync(python, [script, tool, JSON.stringify(payload)], {
      env,
      maxBuffer: 64 * 1024 * 1024,
      windowsHide: true,
    });
    if (stderr) {
      console.error("[mcp_invoke stderr]", stderr.slice(0, 2000));
    }
    const line = stdout.trim().split("\n").filter(Boolean).pop() ?? "{}";
    return JSON.parse(line) as McpDispatchResult;
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[mcp_invoke]", msg);
    return { success: false, error: msg, data: {} };
  }
}

export async function callMcpTool<T = unknown>(
  tool: string,
  payload: Record<string, unknown> = {}
): Promise<McpDispatchResult<T>> {
  if (process.env.MCP_BASE_URL?.trim()) {
    return invokeHttp(tool, payload) as Promise<McpDispatchResult<T>>;
  }
  return invokePython(tool, payload) as Promise<McpDispatchResult<T>>;
}
