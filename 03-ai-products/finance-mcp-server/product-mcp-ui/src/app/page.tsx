"use client";

import Link from "next/link";
import { useQueries, useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { SummaryCard } from "@/components/common/summary-card";
import { MetricGrid } from "@/components/common/metric-grid";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { clientCallTool } from "@/lib/mcp-client";
import { formatMoney } from "@/lib/formatters";
import type { Company, KPIResponse } from "@/types/finance";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { Badge } from "@/components/ui/badge";

type Health = {
  server_status: string;
  db_path: string;
  counts_by_table: Record<string, number>;
};

export default function DashboardPage() {
  const results = useQueries({
    queries: [
      {
        queryKey: ["dash", "health"],
        queryFn: () => clientCallTool<Health>("health_check", {}),
      },
      {
        queryKey: ["dash", "companies"],
        queryFn: () => clientCallTool<{ companies: Company[] }>("list_companies", {}),
      },
      {
        queryKey: ["dash", "import-log"],
        queryFn: async () => {
          const r = await fetch("/api/import-log");
          return r.json() as Promise<{ entries: unknown[] }>;
        },
      },
    ],
  });

  const [healthQ, companiesQ, logQ] = results;
  const firstCompany =
    companiesQ.data?.ok && companiesQ.data.result?.companies?.[0]?.name
      ? companiesQ.data.result.companies[0].name
      : undefined;

  const kpiQ = useQuery({
    queryKey: ["dash", "kpi", firstCompany ?? "__all__"],
    queryFn: () =>
      clientCallTool<KPIResponse>("calculate_kpis", {
        company_name: firstCompany,
        period_start: "2024-01-01",
        period_end: "2024-12-31",
      }),
    enabled: !companiesQ.isLoading && Boolean(companiesQ.data?.ok),
  });

  const loading = healthQ.isLoading || companiesQ.isLoading;
  const err = healthQ.data && !healthQ.data.ok ? healthQ.data.error : companiesQ.data && !companiesQ.data.ok ? companiesQ.data.error : null;

  const health = healthQ.data?.ok ? healthQ.data.result : undefined;
  const kpi = kpiQ.data?.ok ? kpiQ.data.result : undefined;

  return (
    <>
      <Topbar title="Dashboard" badge="Internal finance" />
      <div className="p-6">
        <PageHeader
          title="Executive overview"
          description="Live metrics from product-mcp tools. Configure PRODUCT_MCP_PATH for real data."
        />

        {loading ? <LoadingState /> : null}
        {err ? <ErrorState title="Backend" message={err} technical={JSON.stringify(healthQ.data ?? companiesQ.data)} /> : null}

        {healthQ.data?.mock ? (
          <Badge className="mb-4" variant="secondary">
            Mock mode — set PRODUCT_MCP_PATH + Python env
          </Badge>
        ) : null}

        <MetricGrid>
          <SummaryCard title="Revenue" value={formatMoney(kpi?.total_revenue)} subtitle="YTD sample range" />
          <SummaryCard title="EBITDA" value={formatMoney(kpi?.ebitda)} />
          <SummaryCard title="Cash balance" value={formatMoney(kpi?.cash_balance)} />
          <SummaryCard title="Net cash flow" value={formatMoney(kpi?.net_cash_flow)} />
          <SummaryCard title="AR" value={formatMoney(kpi?.accounts_receivable_total)} />
          <SummaryCard title="AP" value={formatMoney(kpi?.accounts_payable_total)} />
        </MetricGrid>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Alerts & data health</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>
                Open alerts in DB:{" "}
                <strong>{health?.counts_by_table?.alerts ?? "—"}</strong> · Run{" "}
                <Link href="/contracts" className="text-primary underline">
                  contract risk scan
                </Link>{" "}
                to refresh.
              </p>
              <p className="text-muted-foreground">DB: {health?.db_path ?? "—"}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent imports (this UI)</CardTitle>
            </CardHeader>
            <CardContent>
              {logQ.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading…</p>
              ) : !logQ.data?.entries?.length ? (
                <p className="text-sm text-muted-foreground">No imports yet.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {logQ.data.entries.slice(0, 6).map((e: unknown, i: number) => {
                    const x = e as Record<string, unknown>;
                    return (
                      <li key={i} className="flex justify-between gap-2 border-b border-border pb-2">
                        <span className="truncate">{String(x.fileName ?? "")}</span>
                        <span className="shrink-0 text-muted-foreground">{String(x.statementType ?? "")}</span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href="/kpis">Calculate KPIs</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/plan-vs-fact">Plan vs fact</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/liquidity">Liquidity forecast</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/contracts">Contract risk scan</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/import">Upload data</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
