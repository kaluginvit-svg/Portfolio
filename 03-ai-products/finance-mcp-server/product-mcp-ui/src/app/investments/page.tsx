"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/layout/topbar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DataTable, type Column } from "@/components/common/data-table";
import { clientCallTool } from "@/lib/mcp-client";
import { useToolMutation } from "@/hooks/useTool";
import { addProjectSchema } from "@/schemas/investment";
import { ErrorState } from "@/components/common/error-state";
import { ToolRunPanel } from "@/components/common/tool-run-panel";
import { JsonPreview } from "@/components/common/json-preview";
import type { InvestmentProject } from "@/types/finance";
import { LoadingState } from "@/components/common/loading-state";
import { formatMoney } from "@/lib/formatters";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type EvalResult = {
  project_id: number;
  npv: number | null;
  irr: number | null;
  payback_period: number | null;
  profitability_index: number | null;
  recommendation: string;
};

export default function InvestmentsPage() {
  const listQ = useQuery({
    queryKey: ["investments"],
    queryFn: () => clientCallTool<{ records: InvestmentProject[] }>("list_investment_projects", {}),
  });

  const addMut = useToolMutation();
  const evalMut = useToolMutation<EvalResult>();

  const [projectName, setProjectName] = useState("");
  const [companyName, setCompanyName] = useState("Demo Holdings OÜ");
  const [initialInvestment, setInitialInvestment] = useState("1200000");
  const [discountRate, setDiscountRate] = useState("10");
  const [hurdleRate, setHurdleRate] = useState("12");
  const [scenarioJson, setScenarioJson] = useState('{"cash_flows":[320000,340000,360000,380000,400000]}');
  const [notes, setNotes] = useState("");
  const [valErr, setValErr] = useState<string | null>(null);
  const [evalProjectId, setEvalProjectId] = useState("1");
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);

  const rows = listQ.data?.ok && listQ.data.result?.records ? listQ.data.result.records : [];
  const rr = rows as unknown as Record<string, unknown>[];

  const columns: Column<Record<string, unknown>>[] = [
    { key: "id", header: "ID" },
    { key: "project_name", header: "Project" },
    { key: "company_name", header: "Company" },
    { key: "initial_investment", header: "Investment", render: (r) => formatMoney(Number(r.initial_investment)) },
    { key: "discount_rate", header: "Disc. %" },
    { key: "hurdle_rate", header: "Hurdle %" },
    { key: "created_at", header: "Created" },
  ];

  const addProject = () => {
    setValErr(null);
    const p = addProjectSchema.safeParse({
      projectName,
      companyName,
      initialInvestment: Number(initialInvestment),
      discountRate: Number(discountRate),
      hurdleRate: Number(hurdleRate),
      scenarioJson,
      notes: notes || undefined,
    });
    if (!p.success) {
      setValErr(p.error.errors.map((e) => e.message).join("; "));
      return;
    }
    addMut.mutate(
      {
        tool: "add_investment_project",
        payload: {
          project_name: p.data.projectName,
          company_name: p.data.companyName,
          initial_investment: p.data.initialInvestment,
          discount_rate: p.data.discountRate,
          hurdle_rate: p.data.hurdleRate,
          scenario_json: p.data.scenarioJson,
          notes: p.data.notes,
        },
      },
      {
        onSuccess: (r) => {
          if (r.ok) listQ.refetch();
        },
      }
    );
  };

  const evaluate = () => {
    const id = Number(evalProjectId);
    if (!Number.isFinite(id)) return;
    evalMut.mutate(
      { tool: "evaluate_investment", payload: { project_id: id } },
      {
        onSuccess: (r) => {
          if (r.ok && r.result) setEvalResult(r.result as EvalResult);
          else setEvalResult(null);
        },
      }
    );
  };

  return (
    <>
      <Topbar title="Investments" />
      <div className="p-6">
        <PageHeader title="CAPEX & projects" description="list / add / evaluate_investment." />

        {listQ.isLoading ? <LoadingState /> : null}
        {listQ.data && !listQ.data.ok ? <ErrorState title="List failed" message={listQ.data.error || ""} /> : null}

        <DataTable columns={columns} rows={rr} emptyMessage="No projects." />

        <div className="mt-10 grid gap-8 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Add project</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {valErr ? <ErrorState title="Validation" message={valErr} /> : null}
              <div className="space-y-1">
                <Label>Project name</Label>
                <Input value={projectName} onChange={(e) => setProjectName(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Company</Label>
                <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="space-y-1">
                  <Label>Initial</Label>
                  <Input value={initialInvestment} onChange={(e) => setInitialInvestment(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <Label>Discount %</Label>
                  <Input value={discountRate} onChange={(e) => setDiscountRate(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <Label>Hurdle %</Label>
                  <Input value={hurdleRate} onChange={(e) => setHurdleRate(e.target.value)} />
                </div>
              </div>
              <div className="space-y-1">
                <Label>scenario_json</Label>
                <Textarea value={scenarioJson} onChange={(e) => setScenarioJson(e.target.value)} rows={4} className="font-mono text-xs" />
              </div>
              <div className="space-y-1">
                <Label>Notes</Label>
                <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>
              <ToolRunPanel tool="add_investment_project" loading={addMut.isPending} error={addMut.data && !addMut.data.ok ? addMut.data.error : undefined} />
              <Button onClick={addProject} disabled={addMut.isPending}>
                Add project
              </Button>
              {addMut.data?.ok && addMut.data.result ? <JsonPreview data={addMut.data.result} /> : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Evaluate</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <Label>Project ID</Label>
                <Input value={evalProjectId} onChange={(e) => setEvalProjectId(e.target.value)} className="w-32" />
              </div>
              <ToolRunPanel tool="evaluate_investment" loading={evalMut.isPending} error={evalMut.data && !evalMut.data.ok ? evalMut.data.error : undefined} />
              <Button onClick={evaluate} disabled={evalMut.isPending}>
                Evaluate project
              </Button>
              {evalResult ? (
                <ul className="space-y-1 text-sm">
                  <li>
                    <strong>NPV:</strong> {evalResult.npv == null ? "—" : formatMoney(evalResult.npv)}
                  </li>
                  <li>
                    <strong>IRR:</strong> {evalResult.irr == null ? "—" : `${evalResult.irr.toFixed(2)}%`}
                  </li>
                  <li>
                    <strong>Payback:</strong> {evalResult.payback_period == null ? "—" : `${evalResult.payback_period.toFixed(2)} periods`}
                  </li>
                  <li>
                    <strong>PI:</strong> {evalResult.profitability_index == null ? "—" : evalResult.profitability_index.toFixed(3)}
                  </li>
                  <li>
                    <strong>Recommendation:</strong> {evalResult.recommendation}
                  </li>
                </ul>
              ) : null}
              {evalResult ? <JsonPreview data={evalResult} /> : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
