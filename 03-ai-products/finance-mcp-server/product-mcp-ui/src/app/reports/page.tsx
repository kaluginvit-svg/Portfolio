"use client";

import { useState } from "react";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToolMutation } from "@/hooks/useTool";
import { exportFormSchema } from "@/schemas/reports";
import { REPORT_TYPES } from "@/lib/constants";
import { ErrorState } from "@/components/common/error-state";
import { ToolRunPanel } from "@/components/common/tool-run-panel";
import { ReportDownloadCard } from "@/components/common/report-download-card";
import { JsonPreview } from "@/components/common/json-preview";
import type { ReportExportResponse } from "@/types/api";

export default function ReportsPage() {
  const [reportType, setReportType] = useState("kpis");
  const [outputFormat, setOutputFormat] = useState<"json" | "txt">("json");
  const [companyName, setCompanyName] = useState("Demo Holdings OÜ");
  const [periodStart, setPeriodStart] = useState("2024-01-01");
  const [periodEnd, setPeriodEnd] = useState("2024-12-31");
  const [liquidityDays, setLiquidityDays] = useState(90);
  const [paymentStart, setPaymentStart] = useState("");
  const [paymentEnd, setPaymentEnd] = useState("");
  const [projectId, setProjectId] = useState("");
  const [valErr, setValErr] = useState<string | null>(null);

  const mut = useToolMutation<ReportExportResponse>();

  const run = () => {
    setValErr(null);
    const p = exportFormSchema.safeParse({
      reportType,
      outputFormat,
      companyName: companyName || undefined,
      periodStart: periodStart || undefined,
      periodEnd: periodEnd || undefined,
      liquidityDays,
      paymentStart: paymentStart || undefined,
      paymentEnd: paymentEnd || undefined,
      projectId: projectId ? Number(projectId) : undefined,
    });
    if (!p.success) {
      setValErr(p.error.errors.map((e) => e.message).join("; "));
      return;
    }
    const pl: Record<string, unknown> = {
      report_type: p.data.reportType,
      output_format: p.data.outputFormat,
      company_name: p.data.companyName,
      period_start: p.data.periodStart,
      period_end: p.data.periodEnd,
      liquidity_days: p.data.liquidityDays,
      payment_start: p.data.paymentStart,
      payment_end: p.data.paymentEnd,
    };
    if (p.data.reportType === "investment_evaluation") {
      if (p.data.projectId == null) {
        setValErr("project_id required for investment_evaluation");
        return;
      }
      pl.project_id = p.data.projectId;
    }
    mut.mutate({ tool: "export_report", payload: pl });
  };

  const res = mut.data?.ok ? (mut.data.result as ReportExportResponse) : null;

  return (
    <>
      <Topbar title="Reports" />
      <div className="p-6">
        <PageHeader title="Export files" description="export_report writes under product-mcp/data/exports." />

        {valErr ? <ErrorState title="Validation" message={valErr} /> : null}

        <div className="mb-6 grid max-w-3xl gap-4 rounded-lg border border-border bg-card p-4">
          <div className="space-y-1">
            <Label>Report type</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              {REPORT_TYPES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <Label>Output format</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value as "json" | "txt")}
            >
              <option value="json">json</option>
              <option value="txt">txt</option>
            </select>
          </div>
          <div className="space-y-1">
            <Label>Company (optional)</Label>
            <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label>Period start</Label>
              <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Period end</Label>
              <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Liquidity days (liquidity_forecast export)</Label>
            <Input type="number" value={liquidityDays} onChange={(e) => setLiquidityDays(Number(e.target.value))} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label>Payment start</Label>
              <Input type="date" value={paymentStart} onChange={(e) => setPaymentStart(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Payment end</Label>
              <Input type="date" value={paymentEnd} onChange={(e) => setPaymentEnd(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Project ID (investment_evaluation only)</Label>
            <Input value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="1" />
          </div>
          <Button onClick={run} disabled={mut.isPending}>
            {mut.isPending ? "Generating…" : "Generate export"}
          </Button>
        </div>

        <ToolRunPanel tool="export_report" loading={mut.isPending} error={mut.data && !mut.data.ok ? mut.data.error : undefined} mock={mut.data?.mock} />

        {res?.error ? <ErrorState title="Export error" message={res.error} /> : null}
        {res?.path ? <ReportDownloadCard fileName={res.path} /> : null}
        {mut.data?.ok && mut.data.result ? <JsonPreview data={mut.data.result} /> : null}
      </div>
    </>
  );
}
