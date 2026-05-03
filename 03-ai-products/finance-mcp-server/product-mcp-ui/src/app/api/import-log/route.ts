import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getUploadDir } from "@/lib/paths";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const logPath = path.join(getUploadDir(), "import-log.json");
  if (!fs.existsSync(logPath)) {
    return NextResponse.json({ entries: [] });
  }
  try {
    const data = JSON.parse(fs.readFileSync(logPath, "utf-8"));
    return NextResponse.json({ entries: Array.isArray(data) ? data : [] });
  } catch {
    return NextResponse.json({ entries: [] });
  }
}
