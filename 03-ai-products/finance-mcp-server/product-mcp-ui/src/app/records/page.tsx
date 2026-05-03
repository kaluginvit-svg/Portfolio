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
import { clientCallTool } from "@/lib/mcp-client";
import { formatMoney } from "@/lib/formatters";
import type { FinancialRecord } from "@/types/finance";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { downloadCsv } from "@/lib/csv-export";
import { STATEMENT_TYPES } from "@/lib/constants";

export default function RecordsPage() {
  const [statementType, setStatementType] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [category, setCategory] = useState("");
  const [department, setDepartment] = useState("");
  const [project, setProject] = useState("");
  const [counterparty, setCounterparty] = useState("");

  const payload = useMemo(() => {
    const p: Record<string, string> = {};
    if (statementType) p.statement_type = statementType;
    if (companyName) p.company_name = companyName;
    if (startDate) p.start_date = startDate;
    if (endDate) p.end_date = endDate;
    if (category) p.category = category;
    if (department) p.department = department;
    if (project) p.project = project;
    if (counterparty) p.counterparty = counterparty;
    return p;
  }, [statementType, companyName, startDate, endDate, category, department, project, counterparty]);

  const q = useQuery({
    queryKey: ["records", payload],
    queryFn: () => clientCallTool<{ records: FinancialRecord[] }>("list_financial_records", payload),
  });

  const rows = q.data?.ok && q.data.result?.records ? q.data.result.records : [];
  const asRecords = rows as unknown as Record<string, unknown>[];

  const columns: Column<Record<string, unknown>>[] = [
    { key: "record_date", header: "Date" },
    { key: "statement_type", header: "Type" },
    { key: "company_name", header: "Company" },
    { key: "category", header: "Category" },
    { key: "amount", header: "Amount", render: (r) => formatMoney(Number(r.amount), String(r.currency ?? "")) },
    { key: "counterparty", header: "Counterparty" },
  ];

  const exportView = () => {
    const headers = ["record_date", "statement_type", "company_name", "category", "amount", "currency", "counterparty", "department", "project"];
    downloadCsv("financial_records.csv", headers, asRecords);
  };

  return (
    <>
      <Topbar title="Financial records" />
      <div className="p-6">
        <PageHeader title="Ledger & actuals" description="Filtered list_financial_records from MCP." />

        {q.isLoading ? <LoadingState /> : null}
        {q.data && !q.data.ok ? <ErrorState title="Query failed" message={q.data.error || ""} /> : null}

        <FilterBar className="mb-6">
          <div className="space-y-1">
            <Label className="text-xs">Statement</Label>
            <select
              className="flex h-10 rounded-md border border-input bg-card px-2 text-sm"
              value={statementType}
              onChange={(e) => setStatementType(e.target.value)}
            >
              <option value="">All</option>
              {STATEMENT_TYPES.filter((s) => s.value !== "contract").map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Company</Label>
            <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Name" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">From</Label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">To</Label>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Category</Label>
            <Input value={category} onChange={(e) => setCategory(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Department</Label>
            <Input value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Project</Label>
            <Input value={project} onChange={(e) => setProject(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Counterparty</Label>
            <Input value={counterparty} onChange={(e) => setCounterparty(e.target.value)} />
          </div>
          <Button type="button" variant="secondary" onClick={() => q.refetch()}>
            Refresh
          </Button>
          <Button type="button" variant="outline" onClick={exportView} disabled={!rows.length}>
            Export CSV
          </Button>
        </FilterBar>

        <DataTable columns={columns} rows={asRecords} emptyMessage="No records for these filters." />
      </div>
    </>
  );
}
