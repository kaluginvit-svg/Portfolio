"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/common/data-table";
import { clientCallTool } from "@/lib/mcp-client";
import { formatMoney } from "@/lib/formatters";
import type { Contract, ContractRiskScanResult } from "@/types/finance";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { useToolMutation } from "@/hooks/useTool";
import { ToolRunPanel } from "@/components/common/tool-run-panel";
import { AlertList } from "@/components/common/alert-list";
import { flattenContractRisks } from "@/lib/contract-risks-ui";
import { JsonPreview } from "@/components/common/json-preview";

export default function ContractsPage() {
  const [activeOnly, setActiveOnly] = useState(false);
  const [riskData, setRiskData] = useState<ContractRiskScanResult | null>(null);

  const listQ = useQuery({
    queryKey: ["contracts", activeOnly],
    queryFn: () => clientCallTool<{ records: Contract[] }>("list_contracts", { active_only: activeOnly }),
  });

  const scanMut = useToolMutation<ContractRiskScanResult>();

  const rows = listQ.data?.ok && listQ.data.result?.records ? listQ.data.result.records : [];
  const rr = rows as unknown as Record<string, unknown>[];

  const columns: Column<Record<string, unknown>>[] = [
    { key: "contract_name", header: "Contract" },
    { key: "counterparty", header: "Counterparty" },
    { key: "start_date", header: "Start" },
    { key: "end_date", header: "End" },
    { key: "amount", header: "Amount", render: (r) => formatMoney(r.amount == null ? null : Number(r.amount), String(r.currency ?? "")) },
    { key: "payment_terms", header: "Payment terms" },
    { key: "penalty_terms", header: "Penalty" },
  ];

  const runScan = () => {
    scanMut.mutate(
      { tool: "contract_risk_scan", payload: {} },
      {
        onSuccess: (r) => {
          if (r.ok && r.result) setRiskData(r.result as ContractRiskScanResult);
          else setRiskData(null);
        },
      }
    );
  };

  const alertRows = riskData ? flattenContractRisks(riskData) : [];

  return (
    <>
      <Topbar title="Contracts" />
      <div className="p-6">
        <PageHeader title="Legal & commercial" description="list_contracts and contract_risk_scan." />

        <div className="mb-4 flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
            Active only
          </label>
          <Button type="button" variant="secondary" onClick={() => listQ.refetch()}>
            Refresh list
          </Button>
          <Button type="button" onClick={runScan} disabled={scanMut.isPending}>
            {scanMut.isPending ? "Scanning…" : "Run contract risk scan"}
          </Button>
        </div>

        {listQ.isLoading ? <LoadingState /> : null}
        {listQ.data && !listQ.data.ok ? <ErrorState title="List failed" message={listQ.data.error || ""} /> : null}

        <DataTable columns={columns} rows={rr} emptyMessage="No contracts." />

        <ToolRunPanel
          tool="contract_risk_scan"
          loading={scanMut.isPending}
          error={scanMut.data && !scanMut.data.ok ? scanMut.data.error : undefined}
          mock={scanMut.data?.mock}
        />

        {riskData ? (
          <div className="mt-8 space-y-4">
            <p className="text-sm text-muted-foreground">Alerts created in MCP: {riskData.alerts_created}</p>
            <h3 className="text-lg font-semibold">Risk summary (this run)</h3>
            <AlertList rows={alertRows} />
            <JsonPreview data={riskData} title="Scan payload" />
          </div>
        ) : null}
      </div>
    </>
  );
}
