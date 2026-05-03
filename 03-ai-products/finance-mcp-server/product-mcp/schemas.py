"""Pydantic models and JSON Schema helpers for MCP tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolSchemaBundle(BaseModel):
    """Registered tool metadata for introspection."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


def pydantic_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()


# --- Common tool responses ---


class ErrorDetail(BaseModel):
    code: str
    message: str


class ToolResult(BaseModel):
    success: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[ErrorDetail] = Field(default_factory=list)


# --- health_check ---


class HealthCheckOutput(BaseModel):
    server_status: str
    db_path: str
    available_tools: list[str]
    counts_by_table: dict[str, int]


# --- list_companies ---


class CompanyOut(BaseModel):
    id: int
    name: str
    currency: str | None
    created_at: str


class ListCompaniesOutput(BaseModel):
    companies: list[dict[str, Any]]


class GenericRecordsOutput(BaseModel):
    records: list[dict[str, Any]]
    error: str | None = None


class AddInvestmentOutput(BaseModel):
    id: int | None
    project_name: str
    company_id: int | None
    error: str | None = None


# --- import_csv ---


class ImportCsvInput(BaseModel):
    file_path: str
    statement_type: str
    company_name: str | None = None
    version: str | None = None


class ImportCsvOutput(BaseModel):
    imported_count: int
    rejected_count: int
    errors: list[str]


# --- import_contract ---


class ImportContractInput(BaseModel):
    file_path: str


class ImportContractOutput(BaseModel):
    contract_id: int | None
    parsed: dict[str, Any]
    warnings: list[str]


# --- list_financial_records ---


class ListFinancialInput(BaseModel):
    statement_type: str | None = None
    company_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    category: str | None = None
    department: str | None = None
    project: str | None = None
    counterparty: str | None = None


# --- list_budget_records ---


class ListBudgetInput(BaseModel):
    company_name: str | None = None
    version: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    category: str | None = None


# --- list_cash_positions ---


class ListCashInput(BaseModel):
    company_name: str | None = None
    position_date: str | None = None


# --- list_contracts ---


class ListContractsInput(BaseModel):
    active_only: bool = False


# --- calculate_kpis ---


class CalculateKpisInput(BaseModel):
    period_start: str | None = None
    period_end: str | None = None
    company_name: str | None = None


class KpiOutput(BaseModel):
    total_revenue: float = 0.0
    total_opex: float = 0.0
    gross_profit: float = 0.0
    ebitda: float = 0.0
    ebitda_margin: float | None = None
    net_cash_flow: float = 0.0
    accounts_receivable_total: float = 0.0
    accounts_payable_total: float = 0.0
    cash_balance: float = 0.0
    error: str | None = None


# --- plan_vs_fact ---


class PlanVsFactInput(BaseModel):
    period_start: str | None = None
    period_end: str | None = None
    company_name: str | None = None


class PlanVsFactOutput(BaseModel):
    total_plan: float = 0.0
    total_fact: float = 0.0
    variance_abs: float = 0.0
    variance_pct: float | None = None
    breakdown_by_category: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


# --- liquidity_forecast ---


class LiquidityForecastInput(BaseModel):
    days: int = 90
    company_name: str | None = None


class LiquidityForecastOutput(BaseModel):
    opening_cash: float = 0.0
    projected_inflows: float = 0.0
    projected_outflows: float = 0.0
    ending_cash: float = 0.0
    daily_projection: list[dict[str, Any]] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    error: str | None = None


# --- payment_calendar ---


class PaymentCalendarInput(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    company_name: str | None = None


# --- contract_risk_scan ---


class ContractRiskScanOutput(BaseModel):
    expiring_soon: list[dict[str, Any]]
    missing_payment_terms: list[dict[str, Any]]
    missing_penalty_terms: list[dict[str, Any]]
    missing_amount: list[dict[str, Any]]
    no_end_date: list[dict[str, Any]]
    penalty_detected: list[dict[str, Any]]
    alerts_created: int


# --- evaluate_investment ---


class EvaluateInvestmentInput(BaseModel):
    project_id: int


class EvaluateInvestmentOutput(BaseModel):
    project_id: int
    npv: float | None
    irr: float | None
    payback_period: float | None
    profitability_index: float | None
    recommendation: str


# --- add_investment_project ---


class AddInvestmentInput(BaseModel):
    project_name: str
    company_name: str
    initial_investment: float
    discount_rate: float
    hurdle_rate: float
    scenario_json: str
    notes: str | None = None


# --- find_records ---


class FindRecordsInput(BaseModel):
    query: str


# --- export_report ---


class ExportReportInput(BaseModel):
    report_type: str
    output_format: str | None = "json"
    output_path: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    company_name: str | None = None
    liquidity_days: int | None = 90
    payment_start: str | None = None
    payment_end: str | None = None
    project_id: int | None = None


class ExportReportOutput(BaseModel):
    path: str | None
    report_type: str
    error: str | None = None


# --- calculate ---


class CalculateInput(BaseModel):
    expression: str


class CalculateOutput(BaseModel):
    result: float | int | None
    expression: str
    error: str | None = None


def bundle(
    name: str,
    description: str,
    input_model: type[BaseModel],
    output_model: type[BaseModel],
) -> ToolSchemaBundle:
    return ToolSchemaBundle(
        name=name,
        description=description,
        input_schema=pydantic_json_schema(input_model),
        output_schema=pydantic_json_schema(output_model),
    )


def tool_bundles() -> list[ToolSchemaBundle]:
    """All tools for introspection."""

    class EmptyInput(BaseModel):
        pass

    return [
        bundle(
            "health_check",
            "Server status, DB path, tool list, and row counts per table.",
            EmptyInput,
            HealthCheckOutput,
        ),
        bundle(
            "list_companies",
            "List all companies.",
            EmptyInput,
            ListCompaniesOutput,
        ),
        bundle(
            "import_csv",
            "Import a CSV into financial_records or budget_records.",
            ImportCsvInput,
            ImportCsvOutput,
        ),
        bundle(
            "import_contract",
            "Import contract from TXT or PDF; extract fields heuristically.",
            ImportContractInput,
            ImportContractOutput,
        ),
        bundle(
            "list_financial_records",
            "Filter financial_records.",
            ListFinancialInput,
            GenericRecordsOutput,
        ),
        bundle(
            "list_budget_records",
            "Filter budget_records.",
            ListBudgetInput,
            GenericRecordsOutput,
        ),
        bundle(
            "list_cash_positions",
            "Filter cash_positions.",
            ListCashInput,
            GenericRecordsOutput,
        ),
        bundle(
            "list_contracts",
            "List contracts; optional active_only.",
            ListContractsInput,
            GenericRecordsOutput,
        ),
        bundle(
            "list_investment_projects",
            "List investment projects.",
            EmptyInput,
            GenericRecordsOutput,
        ),
        bundle(
            "calculate_kpis",
            "Compute KPIs for a period and optional company.",
            CalculateKpisInput,
            KpiOutput,
        ),
        bundle(
            "plan_vs_fact",
            "Compare budget vs actual financial_records.",
            PlanVsFactInput,
            PlanVsFactOutput,
        ),
        bundle(
            "liquidity_forecast",
            "Simple liquidity projection over N days.",
            LiquidityForecastInput,
            LiquidityForecastOutput,
        ),
        bundle(
            "payment_calendar",
            "Payments and receipts with direction and overdue flag.",
            PaymentCalendarInput,
            GenericRecordsOutput,
        ),
        bundle(
            "contract_risk_scan",
            "Scan contracts for risks and persist alerts.",
            EmptyInput,
            ContractRiskScanOutput,
        ),
        bundle(
            "evaluate_investment",
            "NPV, IRR, payback, PI for a project.",
            EvaluateInvestmentInput,
            EvaluateInvestmentOutput,
        ),
        bundle(
            "add_investment_project",
            "Create investment project row.",
            AddInvestmentInput,
            AddInvestmentOutput,
        ),
        bundle(
            "find_records",
            "Search across financial fields and contracts.",
            FindRecordsInput,
            GenericRecordsOutput,
        ),
        bundle(
            "export_report",
            "Export a report file to data/exports.",
            ExportReportInput,
            ExportReportOutput,
        ),
        bundle(
            "calculate",
            "Safe arithmetic expression evaluator.",
            CalculateInput,
            CalculateOutput,
        ),
    ]


def introspection_json() -> str:
    """Same payload as historically; implemented via registry to avoid duplicate dump logic."""
    import registry as _registry

    return _registry.introspection_json()
