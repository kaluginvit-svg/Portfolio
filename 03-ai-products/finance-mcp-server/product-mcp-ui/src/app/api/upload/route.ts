import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { randomUUID } from "crypto";
import { appendImportLog, getUploadDir } from "@/lib/paths";
import { xlsxBufferToCsv } from "@/lib/xlsx-to-csv";
import { callMcpTool } from "@/lib/mcp-server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function previewRows(filePath: string, maxLines = 8): string[][] {
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    return raw
      .split(/\r?\n/)
      .filter((l) => l.length > 0)
      .slice(0, maxLines)
      .map((line) => {
        const parts: string[] = [];
        let cur = "";
        let q = false;
        for (let i = 0; i < line.length; i++) {
          const c = line[i];
          if (c === '"') {
            q = !q;
            continue;
          }
          if (!q && c === ",") {
            parts.push(cur.trim());
            cur = "";
            continue;
          }
          cur += c;
        }
        parts.push(cur.trim());
        return parts;
      });
  } catch {
    return [];
  }
}

export async function POST(req: Request) {
  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid form data" }, { status: 400 });
  }

  const file = form.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ ok: false, error: "Missing file" }, { status: 400 });
  }

  const statementType = String(form.get("statement_type") || "").toLowerCase();
  const companyName = form.get("company_name") ? String(form.get("company_name")) : undefined;
  const version = form.get("version") ? String(form.get("version")) : undefined;

  const ext = path.extname(file.name).toLowerCase();
  const allowed = [".csv", ".xlsx", ".xls", ".pdf", ".txt", ".md"];
  if (!allowed.includes(ext)) {
    return NextResponse.json({ ok: false, error: `Unsupported file type: ${ext}` }, { status: 400 });
  }

  const buf = Buffer.from(await file.arrayBuffer());
  const uploadDir = getUploadDir();
  const storedName = `${randomUUID()}_${path.basename(file.name)}`;
  const savedPath = path.join(uploadDir, storedName);
  fs.writeFileSync(savedPath, buf);

  let pathForMcp = savedPath;
  let conversionNote: string | undefined;

  if (statementType === "contract") {
    if (![".pdf", ".txt", ".md"].includes(ext)) {
      return NextResponse.json(
        {
          ok: false,
          error: "For contract import use PDF or plain text (.txt / .md).",
        },
        { status: 400 }
      );
    }
    const raw = await callMcpTool("import_contract", { file_path: pathForMcp });
    const success = raw.success && raw.success === true;
    const result = success && "result" in raw ? raw.result : undefined;
    appendImportLog({
      fileName: file.name,
      statementType: "contract",
      success,
      contractId: result && typeof result === "object" && result !== null && "contract_id" in result ? (result as { contract_id: number }).contract_id : null,
    });
    return NextResponse.json({
      ok: success,
      tool: "import_contract",
      result,
      error: success ? undefined : "error" in raw ? raw.error : "Import failed",
      warnings: result && typeof result === "object" && result !== null && "warnings" in result ? (result as { warnings: string[] }).warnings : [],
      preview: [],
    });
  }

  if (ext === ".xlsx" || ext === ".xls") {
    try {
      const csv = xlsxBufferToCsv(buf);
      const csvPath = savedPath.replace(/\.(xlsx|xls)$/i, ".csv");
      fs.writeFileSync(csvPath, csv, "utf-8");
      pathForMcp = csvPath;
      conversionNote = "Spreadsheet converted to CSV for import_csv.";
    } catch (e) {
      return NextResponse.json(
        { ok: false, error: e instanceof Error ? e.message : "XLSX conversion failed" },
        { status: 400 }
      );
    }
  }

  const validTabular = ["pnl", "cashflow", "balance", "ap", "ar", "payments", "kpi", "budget"];
  if (!validTabular.includes(statementType)) {
    return NextResponse.json({ ok: false, error: "Select a statement type for tabular import." }, { status: 400 });
  }

  const raw = await callMcpTool("import_csv", {
    file_path: pathForMcp,
    statement_type: statementType,
    company_name: companyName,
    version: version || undefined,
  });

  const success = raw.success === true;
  const result = success && "result" in raw ? raw.result : undefined;
  const preview = ext === ".csv" || conversionNote ? previewRows(pathForMcp) : [];

  appendImportLog({
    fileName: file.name,
    statementType,
    companyName,
    importedCount:
      result && typeof result === "object" && result !== null && "imported_count" in result
        ? (result as { imported_count: number }).imported_count
        : undefined,
    rejectedCount:
      result && typeof result === "object" && result !== null && "rejected_count" in result
        ? (result as { rejected_count: number }).rejected_count
        : undefined,
    success,
  });

  return NextResponse.json({
    ok: success,
    tool: "import_csv",
    result,
    error: success ? undefined : "error" in raw ? raw.error : "Import failed",
    conversionNote,
    preview,
  });
}
