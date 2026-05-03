"use client";

import { useState } from "react";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SummaryCard } from "@/components/common/summary-card";
import { MetricGrid } from "@/components/common/metric-grid";
import { DataTable, type Column } from "@/components/common/data-table";
import { CommentaryBox } from "@/components/common/commentary-box";
import { useToolMutation } from "@/hooks/useTool";
import { ErrorState } from "@/components/common/error-state";
import { ToolRunPanel } from "@/components/common/tool-run-panel";
import { JsonPreview } from "@/components/common/json-preview";
import { formatMoney, formatPercentPoints } from "@/lib/formatters";
import { buildPlanFactCommentary } from "@/lib/plan-fact-commentary";
import type { PlanVsFactResponse } from "@/types/finance";

export default function PlanVsFactPage() {
  const [companyName, setCompanyName] = useState("Demo Holdings OÜ");
  const [periodStart, setPeriodStart] = useState("2024-01-01");
  const [periodEnd, setPeriodEnd] = useState("2024-12-31");
  const [data, setData] = useState<PlanVsFactResponse | null>(null);

  const mut = useToolMutation<PlanVsFactResponse>();

  const run = () => {
    mut.mutate(
      {
        tool: "plan_vs_fact",
        payload: {
          company_name: companyName || undefined,
          period_start: periodStart || undefined,
          period_end: periodEnd || undefined,
        },
      },
      {
        onSuccess: (r) => {
          if (!r.ok) {
            setData(null);
            return;
          }
          setData((r.result as PlanVsFactResponse) ?? null);
        },
      }
    );
  };

  const breakdown = data?.breakdown_by_category ?? [];
  const br = breakdown as unknown as Record<string, unknown>[];
  const columns: Column<Record<string, unknown>>[] = [
    { key: "category", header: "Category" },
    { key: "plan", header: "Plan", render: (r) => formatMoney(Number(r.plan)) },
    { key: "fact", header: "Fact", render: (r) => formatMoney(Number(r.fact)) },
    { key: "variance_abs", header: "Var (abs)", render: (r) => formatMoney(Number(r.variance_abs)) },
    {
      key: "variance_pct",
      header: "Var %",
      render: (r) => (r.variance_pct == null ? "—" : formatPercentPoints(Number(r.variance_pct))),
    },
  ];

  return (
    <>
      <Topbar title="Plan vs fact" />
      <div className="p-6">
        <PageHeader title="Budget variance" description="plan_vs_fact from MCP (budget vs P&amp;L fact)." />

        <div className="mb-6 flex flex-wrap items-end gap-4 rounded-lg border border-border bg-card p-4">
          <div className="space-y-1">
            <Label>Company</Label>
            <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="w-56" />
          </div>
          <div className="space-y-1">
            <Label>From</Label>
            <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>To</Label>
            <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
          </div>
          <Button onClick={run} disabled={mut.isPending}>
            {mut.isPending ? "Running…" : "Run analysis"}
          </Button>
        </div>

        <ToolRunPanel tool="plan_vs_fact" loading={mut.isPending} error={mut.data && !mut.data.ok ? mut.data.error : mut.error?.message} mock={mut.data?.mock} />

        {data?.error ? <ErrorState title="Tool returned error" message={data.error} /> : null}

        {data && !data.error ? (
          <>
            <MetricGrid>
              <SummaryCard title="Total plan" value={formatMoney(data.total_plan)} />
              <SummaryCard title="Total fact" value={formatMoney(data.total_fact)} />
              <SummaryCard title="Variance (abs)" value={formatMoney(data.variance_abs)} />
              <SummaryCard title="Variance %" value={formatPercentPoints(data.variance_pct ?? null)} />
            </MetricGrid>
            <div className="mt-6">
              <CommentaryBox text={buildPlanFactCommentary(data)} />
            </div>
            <h3 className="mb-3 mt-8 text-lg font-semibold">By category</h3>
            <DataTable columns={columns} rows={br} emptyMessage="No breakdown rows." />
            <div className="mt-6">
              <JsonPreview data={data} />
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}
