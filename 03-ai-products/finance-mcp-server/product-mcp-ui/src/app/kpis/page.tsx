"use client";

import { useState } from "react";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MetricGrid } from "@/components/common/metric-grid";
import { SummaryCard } from "@/components/common/summary-card";
import { useToolMutation } from "@/hooks/useTool";
import { kpiFormSchema } from "@/schemas/kpis";
import { ErrorState } from "@/components/common/error-state";
import { ToolRunPanel } from "@/components/common/tool-run-panel";
import { JsonPreview } from "@/components/common/json-preview";
import { formatMoney, formatDecimalAsPercent } from "@/lib/formatters";
import type { KPIResponse } from "@/types/finance";

function formatMargin(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return formatDecimalAsPercent(n);
}

export default function KpisPage() {
  const [companyName, setCompanyName] = useState("Demo Holdings OÜ");
  const [periodStart, setPeriodStart] = useState("2024-01-01");
  const [periodEnd, setPeriodEnd] = useState("2024-12-31");
  const [valErr, setValErr] = useState<string | null>(null);
  const [data, setData] = useState<KPIResponse | null>(null);

  const mut = useToolMutation<KPIResponse>();

  const run = () => {
    setValErr(null);
    const p = kpiFormSchema.safeParse({ companyName, periodStart, periodEnd });
    if (!p.success) {
      setValErr(p.error.errors.map((e) => e.message).join("; "));
      return;
    }
    mut.mutate(
      {
        tool: "calculate_kpis",
        payload: {
          company_name: p.data.companyName || undefined,
          period_start: p.data.periodStart || undefined,
          period_end: p.data.periodEnd || undefined,
        },
      },
      {
        onSuccess: (r) => {
          if (!r.ok) {
            setData(null);
            return;
          }
          setData((r.result as KPIResponse) ?? null);
        },
      }
    );
  };

  return (
    <>
      <Topbar title="KPIs" />
      <div className="p-6">
        <PageHeader title="Performance metrics" description="calculate_kpis tool output." />
        {valErr ? <ErrorState title="Validation" message={valErr} /> : null}

        <div className="mb-6 flex flex-wrap items-end gap-4 rounded-lg border border-border bg-card p-4">
          <div className="space-y-1">
            <Label>Company</Label>
            <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="w-56" />
          </div>
          <div className="space-y-1">
            <Label>Period start</Label>
            <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>Period end</Label>
            <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
          </div>
          <Button onClick={run} disabled={mut.isPending}>
            {mut.isPending ? "Running…" : "Calculate KPIs"}
          </Button>
        </div>

        <ToolRunPanel tool="calculate_kpis" loading={mut.isPending} error={mut.data && !mut.data.ok ? mut.data.error : mut.error?.message} mock={mut.data?.mock}>
          {data?.error ? <p className="text-sm text-destructive">{data.error}</p> : null}
        </ToolRunPanel>

        {data ? (
          <>
            <MetricGrid>
              <SummaryCard title="Total revenue" value={formatMoney(data.total_revenue)} />
              <SummaryCard title="Total OPEX" value={formatMoney(data.total_opex)} />
              <SummaryCard title="Gross profit" value={formatMoney(data.gross_profit)} />
              <SummaryCard title="EBITDA" value={formatMoney(data.ebitda)} />
              <SummaryCard title="EBITDA margin" value={formatMargin(data.ebitda_margin)} />
              <SummaryCard title="Net cash flow" value={formatMoney(data.net_cash_flow)} />
              <SummaryCard title="AR" value={formatMoney(data.accounts_receivable_total)} />
              <SummaryCard title="AP" value={formatMoney(data.accounts_payable_total)} />
              <SummaryCard title="Cash balance" value={formatMoney(data.cash_balance)} />
            </MetricGrid>
            <div className="mt-6">
              <JsonPreview data={data} />
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}
