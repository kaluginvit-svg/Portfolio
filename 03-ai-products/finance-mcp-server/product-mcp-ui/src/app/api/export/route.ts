import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getProductMcpExportsDir } from "@/lib/paths";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const name = searchParams.get("file");
  if (!name || name.includes("..") || name.includes("/") || name.includes("\\")) {
    return NextResponse.json({ error: "Invalid file name" }, { status: 400 });
  }

  const exportsRoot = getProductMcpExportsDir();
  if (!exportsRoot || !fs.existsSync(exportsRoot)) {
    return NextResponse.json({ error: "Exports directory not configured or missing" }, { status: 503 });
  }

  const resolvedRoot = path.resolve(exportsRoot);
  const full = path.resolve(path.join(resolvedRoot, path.basename(name)));
  if (!full.startsWith(resolvedRoot)) {
    return NextResponse.json({ error: "Path not allowed" }, { status: 403 });
  }

  if (!fs.existsSync(full)) {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }

  const body = fs.readFileSync(full);
  const ct = name.endsWith(".json") ? "application/json" : "text/plain";
  return new NextResponse(body, {
    headers: {
      "Content-Type": ct,
      "Content-Disposition": `attachment; filename="${path.basename(name)}"`,
    },
  });
}
