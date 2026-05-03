"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { FilterBar } from "@/components/common/filter-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DataTable, type Column } from "@/components/common/data-table";
import { Badge } from "@/components/ui/badge";
import { clientCallTool } from "@/lib/mcp-client";
import { formatMoney } from "@/lib/formatters";
import type { PaymentCalendarRow } from "@/types/finance";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";

export default function PaymentsPage() {
  const [companyName, setCompanyName] = useState("Demo Holdings OÜ");
  const [startDate, setStartDate] = useState("2024-06-01");
  const [endDate, setEndDate] = useState("2024-12-31");

  const payload = useMemo(
    () => ({
      company_name: companyName || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
    [companyName, startDate, endDate]
  );

  const q = useQuery({
    queryKey: ["payments", payload],
    queryFn: () => clientCallTool<{ records: PaymentCalendarRow[] }>("payment_calendar", payload),
  });

  const rows = q.data?.ok && q.data.result?.records ? q.data.result.records : [];
  const rr = rows as unknown as Record<string, unknown>[];

  const columns: Column<Record<string, unknown>>[] = [
    { key: "record_date", header: "Date" },
    {
      key: "direction",
      header: "Direction",
      render: (r) => (
        <Badge variant={r.direction === "inflow" ? "default" : "secondary"}>{String(r.direction)}</Badge>
      ),
    },
    { key: "counterparty", header: "Counterparty / category", render: (r) => String(r.counterparty || r.category || "—") },
    { key: "amount", header: "Amount", render: (r) => formatMoney(Number(r.amount), String(r.currency ?? "")) },
    {
      key: "overdue",
      header: "Overdue",
      render: (r) => (r.overdue ? <Badge variant="destructive">Yes</Badge> : <span className="text-muted-foreground">No</span>),
    },
    { key: "source_file", header: "Source" },
  ];

  return (
    <>
      <Topbar title="Payment calendar" />
      <div className="p-6">
        <PageHeader title="Inflows & outflows" description="payment_calendar tool." />

        <FilterBar className="mb-6">
          <div className="space-y-1">
            <Label className="text-xs">Company</Label>
            <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="w-56" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">From</Label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">To</Label>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <Button type="button" variant="secondary" onClick={() => q.refetch()}>
            Refresh
          </Button>
        </FilterBar>

        {q.isLoading ? <LoadingState /> : null}
        {q.data && !q.data.ok ? <ErrorState title="Query failed" message={q.data.error || ""} /> : null}

        <DataTable columns={columns} rows={rr} emptyMessage="No payments in range." />
      </div>
    </>
  );
}
