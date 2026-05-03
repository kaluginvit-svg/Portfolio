"use client";

import { useState } from "react";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { FileUploadZone } from "@/components/common/file-upload-zone";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUploadMutation } from "@/hooks/useUpload";
import { STATEMENT_TYPES } from "@/lib/constants";
import { ErrorState } from "@/components/common/error-state";
import { JsonPreview } from "@/components/common/json-preview";
import { importFormSchema } from "@/schemas/import";

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [statementType, setStatementType] = useState("pnl");
  const [companyName, setCompanyName] = useState("");
  const [version, setVersion] = useState("v2024.1");
  const [validationError, setValidationError] = useState<string | null>(null);

  const upload = useUploadMutation();

  const onSubmit = () => {
    setValidationError(null);
    const parsed = importFormSchema.safeParse({
      statementType,
      companyName: companyName || undefined,
      version: version || undefined,
    });
    if (!parsed.success) {
      setValidationError(parsed.error.errors.map((e) => e.message).join("; "));
      return;
    }
    if (!file) {
      setValidationError("Choose a file.");
      return;
    }
    if (statementType !== "contract" && !companyName.trim()) {
      setValidationError("Company is required for tabular imports.");
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("statement_type", statementType);
    if (companyName) fd.append("company_name", companyName);
    if (version && statementType === "budget") fd.append("version", version);
    upload.mutate(fd);
  };

  const res = upload.data;

  return (
    <>
      <Topbar title="Data import" />
      <div className="p-6">
        <PageHeader
          title="Import files"
          description="Upload CSV, Excel, or contract documents. Tabular files are converted or passed to import_csv; contracts use import_contract."
        />

        {validationError ? <ErrorState title="Validation" message={validationError} /> : null}
        {upload.isError ? (
          <ErrorState title="Upload failed" message={upload.error instanceof Error ? upload.error.message : "Error"} />
        ) : null}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>File</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FileUploadZone
                accept=".csv,.xlsx,.xls,.pdf,.txt,.md"
                file={file}
                onFile={setFile}
                disabled={upload.isPending}
              />
              <div className="space-y-2">
                <Label>Statement type</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
                  value={statementType}
                  onChange={(e) => setStatementType(e.target.value)}
                >
                  {STATEMENT_TYPES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Company (required for tabular)</Label>
                <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Demo Holdings OÜ" />
              </div>
              {statementType === "budget" ? (
                <div className="space-y-2">
                  <Label>Budget version</Label>
                  <Input value={version} onChange={(e) => setVersion(e.target.value)} />
                </div>
              ) : null}
              <Button onClick={onSubmit} disabled={upload.isPending}>
                {upload.isPending ? "Importing…" : "Run import"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Result</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {res?.conversionNote ? <p className="text-sm text-muted-foreground">{res.conversionNote}</p> : null}
              {res?.ok === false ? <ErrorState title="Import error" message={res.error || "Failed"} /> : null}
              {res?.ok && res.result && typeof res.result === "object" && "imported_count" in res.result ? (
                <div className="text-sm">
                  {(() => {
                    const r = res.result as unknown as {
                      imported_count?: number;
                      rejected_count?: number;
                      errors?: string[];
                    };
                    return (
                      <>
                        <p>
                          Imported: <strong>{String(r.imported_count ?? 0)}</strong>
                        </p>
                        <p>
                          Rejected: <strong>{String(r.rejected_count ?? 0)}</strong>
                        </p>
                        {Array.isArray(r.errors) && r.errors.length > 0 ? (
                          <ul className="mt-2 list-disc pl-5 text-destructive">
                            {r.errors.slice(0, 20).map((e, i) => (
                              <li key={i}>{e}</li>
                            ))}
                          </ul>
                        ) : null}
                      </>
                    );
                  })()}
                </div>
              ) : null}
              {res?.ok && res.result && typeof res.result === "object" && "warnings" in res.result ? (
                <ul className="list-disc pl-5 text-sm text-muted-foreground">
                  {(((res.result as unknown as { warnings?: string[] }).warnings) || []).map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              ) : null}
              {res?.preview && res.preview.length > 0 ? (
                <div>
                  <p className="mb-2 text-sm font-medium">Preview (first rows)</p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {res.preview[0]?.map((_, ci) => (
                          <TableHead key={ci} className="text-xs">
                            Col {ci + 1}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {res.preview.map((row, ri) => (
                        <TableRow key={ri}>
                          {row.map((c, ci) => (
                            <TableCell key={ci} className="text-xs">
                              {c}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : null}
              {res ? <JsonPreview data={res} title="Full response" /> : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
