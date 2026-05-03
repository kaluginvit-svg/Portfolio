export type Company = {
  id: number;
  name: string;
  currency: string | null;
  created_at: string;
};

export type FinancialRecord = {
  id: number;
  company_id: number;
  record_date: string;
  statement_type: string;
  category: string | null;
  subcategory: string | null;
  counterparty: string | null;
  project: string | null;
  department: string | null;
  region: string | null;
  product: string | null;
  amount: number;
  currency: string | null;
  source_file: string | null;
  created_at: string;
  company_name?: string;
};

export type BudgetRecord = {
  id: number;
  company_id: number;
  record_date: string;
  statement_type: string;
  category: string | null;
  subcategory: string | null;
  project: string | null;
  department: string | null;
  region: string | null;
  product: string | null;
  amount: number;
  currency: string | null;
  version: string | null;
  source_file: string | null;
  created_at: string;
  company_name?: string;
};

export type CashPosition = {
  id: number;
  company_id: number;
  position_date: string;
  bank_account: string | null;
  bank_name: string | null;
  amount: number;
  currency: string | null;
  source_file: string | null;
  created_at: string;
  company_name?: string;
};

export type Contract = {
  id: number;
  contract_name: string | null;
  counterparty: string | null;
  start_date: string | null;
  end_date: string | null;
  payment_terms: string | null;
  penalty_terms: string | null;
  currency: string | null;
  amount: number | null;
  source_file: string | null;
  raw_text: string | null;
  created_at: string;
};

export type ContractRisk = {
  category: string;
  severity: string;
  contract: Contract;
};

export type InvestmentProject = {
  id: number;
  project_name: string;
  company_id: number | null;
  initial_investment: number | null;
  discount_rate: number | null;
  hurdle_rate: number | null;
  currency: string | null;
  scenario_json: string | null;
  notes: string | null;
  created_at: string;
  company_name?: string | null;
};

export type KPIResponse = {
  total_revenue: number;
  total_opex: number;
  gross_profit: number;
  ebitda: number;
  ebitda_margin: number | null;
  net_cash_flow: number;
  accounts_receivable_total: number;
  accounts_payable_total: number;
  cash_balance: number;
  error?: string | null;
};

export type PlanVsFactBreakdown = {
  category: string;
  plan: number;
  fact: number;
  variance_abs: number;
  variance_pct: number | null;
};

export type PlanVsFactResponse = {
  total_plan: number;
  total_fact: number;
  variance_abs: number;
  variance_pct: number | null;
  breakdown_by_category: PlanVsFactBreakdown[];
  error?: string | null;
};

export type LiquidityDay = {
  date: string;
  net_flow: number;
  inflow: number;
  outflow: number;
  running_cash: number;
};

export type LiquidityForecastResponse = {
  opening_cash: number;
  projected_inflows: number;
  projected_outflows: number;
  ending_cash: number;
  daily_projection: LiquidityDay[];
  risk_flags: string[];
  error?: string | null;
};

export type PaymentCalendarRow = FinancialRecord & {
  direction: string;
  overdue: boolean;
};

export type ContractRiskScanResult = {
  expiring_soon: Contract[];
  missing_payment_terms: Contract[];
  missing_penalty_terms: Contract[];
  missing_amount: Contract[];
  no_end_date: Contract[];
  penalty_detected: Contract[];
  alerts_created: number;
};
