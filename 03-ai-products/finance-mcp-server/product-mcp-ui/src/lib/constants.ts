export const STATEMENT_TYPES = [
  { value: "pnl", label: "P&L" },
  { value: "cashflow", label: "Cash flow" },
  { value: "balance", label: "Balance" },
  { value: "ap", label: "Accounts payable" },
  { value: "ar", label: "Accounts receivable" },
  { value: "payments", label: "Payments" },
  { value: "kpi", label: "KPI" },
  { value: "budget", label: "Budget" },
  { value: "contract", label: "Contract (PDF/TXT)" },
] as const;

export const REPORT_TYPES = [
  { value: "kpis", label: "KPIs" },
  { value: "plan_vs_fact", label: "Plan vs fact" },
  { value: "liquidity_forecast", label: "Liquidity forecast" },
  { value: "payment_calendar", label: "Payment calendar" },
  { value: "contract_risks", label: "Contract risks" },
  { value: "investment_evaluation", label: "Investment evaluation" },
] as const;

export const PAGE_SIZE = 25;
