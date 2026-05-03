import { NextResponse } from "next/server";
import { toolRequestSchema } from "@/schemas/tools";
import { callMcpTool } from "@/lib/mcp-server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { ok: false, tool: "", payload: {}, error: "Invalid JSON body" },
      { status: 400 }
    );
  }

  const parsed = toolRequestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      {
        ok: false,
        tool: "",
        payload: {},
        error: "Validation failed",
        technical: JSON.stringify(parsed.error.flatten()),
      },
      { status: 400 }
    );
  }

  const { tool, payload } = parsed.data;
  const mockMode =
    !process.env.MCP_BASE_URL?.trim() && !process.env.PRODUCT_MCP_PATH?.trim();

  try {
    const raw = await callMcpTool(tool, payload as Record<string, unknown>);
    const success = Boolean(raw.success);
    if (!success) {
      return NextResponse.json({
        ok: false,
        tool,
        payload: payload as Record<string, unknown>,
        success: false,
        error: "error" in raw ? raw.error : "MCP error",
        mock: mockMode,
      });
    }
    return NextResponse.json({
      ok: true,
      tool,
      payload: payload as Record<string, unknown>,
      success: true,
      result: "result" in raw ? raw.result : undefined,
      mock: mockMode,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      {
        ok: false,
        tool,
        payload: payload as Record<string, unknown>,
        error: msg,
        technical: msg,
        mock: mockMode,
      },
      { status: 500 }
    );
  }
}
