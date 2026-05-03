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
import { ForecastChart } from "@/components/charts/forecast-chart";
import { useToolMutation } from "@/hooks/useTool";
import { ToolRunPanel } from "@/components/common/tool-run-panel";
import { ErrorState } from "@/components/common/error-state";
import { JsonPreview } from "@/components/common/json-preview";
import { liquidityFormSchema } from "@/schemas/liquidity";
import { formatMoney } from "@/lib/formatters";
import type { LiquidityDay, LiquidityForecastResponse } from "@/types/finance";
import { Badge } from "@/components/ui/badge";

export default function LiquidityPage() {
  const [companyName, setCompanyName] = useState("Demo Holdings OÜ");
  const [days, setDays] = useState(90);
  const [valErr, setValErr] = useState<string | null>(null);
  const [data, setData] = useState<LiquidityForecastResponse | null>(null);

  const mut = useToolMutation<LiquidityForecastResponse>();

  const run = () => {
    setValErr(null);
    const p = liquidityFormSchema.safeParse({ companyName, days });
    if (!p.success) {
      setValErr(p.error.errors.map((e) => e.message).join("; "));
      return;
    }
    mut.mutate(
      {
        tool: "liquidity_forecast",
        payload: {
          company_name: p.data.companyName || undefined,
          days: p.data.days,
        },
      },
      {
        onSuccess: (r) => {
          if (!r.ok) {
            setData(null);
            return;
          }
          setData((r.result as LiquidityForecastResponse) ?? null);
        },
      }
    );
  };

  const proj = data?.daily_projection ?? [];
  const pr = proj as unknown as Record<string, unknown>[];
  const columns: Column<Record<string, unknown>>[] = [
    { key: "date", header: "Date" },
    { key: "inflow", header: "Inflow", render: (r) => formatMoney(Number(r.inflow)) },
    { key: "outflow", header: "Outflow", render: (r) => formatMoney(Number(r.outflow)) },
    { key: "net_flow", header: "Net", render: (r) => formatMoney(Number(r.net_flow)) },
    { key: "running_cash", header: "Running cash", render: (r) => formatMoney(Number(r.running_cash)) },
  ];

  return (
    <>
      <Topbar title="Liquidity" />
      <div className="p-6">
        <PageHeader title="Cash forecast" description="liquidity_forecast tool — scheduled payments + fallback patterns." />

        {valErr ? <ErrorState title="Validation" message={valErr} /> : null}

        <div className="mb-6 flex flex-wrap items-end gap-4 rounded-lg border border-border bg-card p-4">
          <div className="space-y-1">
            <Label>Company</Label>
            <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="w-56" />
          </div>
          <div className="space-y-1">
            <Label>Horizon (days)</Label>
            <Input type="number" min={1} max={730} value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-28" />
          </div>
          <Button onClick={run} disabled={mut.isPending}>
            {mut.isPending ? "Building…" : "Build forecast"}
          </Button>
        </div>

        <ToolRunPanel tool="liquidity_forecast" loading={mut.isPending} error={mut.data && !mut.data.ok ? mut.data.error : mut.error?.message} mock={mut.data?.mock} />

        {data?.error ? <ErrorState title="Error" message={data.error} /> : null}

        {data && !data.error ? (
          <>
            <MetricGrid>
              <SummaryCard title="Opening cash" value={formatMoney(data.opening_cash)} />
              <SummaryCard title="Projected inflows" value={formatMoney(data.projected_inflows)} />
              <SummaryCard title="Projected outflows" value={formatMoney(data.projected_outflows)} />
              <SummaryCard title="Ending cash" value={formatMoney(data.ending_cash)} />
            </MetricGrid>
            <div className="mt-4 flex flex-wrap gap-2">
              {(data.risk_flags ?? []).map((f) => (
                <Badge key={f} variant="destructive">
                  {f}
                </Badge>
              ))}
            </div>
            <h3 className="mb-3 mt-8 text-lg font-semibold">Cash trend</h3>
            <ForecastChart data={proj as LiquidityDay[]} />
            <h3 className="mb-3 mt-8 text-lg font-semibold">Daily projection</h3>
            <DataTable columns={columns} rows={pr} pageSize={31} emptyMessage="No projection rows." />
            <div className="mt-6">
              <JsonPreview data={data} />
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}
