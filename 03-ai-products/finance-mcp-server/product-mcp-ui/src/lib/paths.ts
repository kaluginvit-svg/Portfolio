import path from "path";
import fs from "fs";

export function getUploadDir(): string {
  const d = process.env.UPLOAD_DIR?.trim() || path.join(process.cwd(), "data", "uploads");
  const abs = path.resolve(d);
  fs.mkdirSync(abs, { recursive: true });
  return abs;
}

export function getProductMcpExportsDir(): string | null {
  const root = process.env.PRODUCT_MCP_PATH?.trim();
  if (!root) return null;
  const exp = path.resolve(root, "data", "exports");
  return exp;
}

export function appendImportLog(entry: Record<string, unknown>): void {
  const logPath = path.join(getUploadDir(), "import-log.json");
  let arr: unknown[] = [];
  try {
    if (fs.existsSync(logPath)) {
      arr = JSON.parse(fs.readFileSync(logPath, "utf-8"));
      if (!Array.isArray(arr)) arr = [];
    }
  } catch {
    arr = [];
  }
  arr.unshift({ ...entry, at: new Date().toISOString() });
  fs.writeFileSync(logPath, JSON.stringify(arr.slice(0, 100), null, 2), "utf-8");
}
