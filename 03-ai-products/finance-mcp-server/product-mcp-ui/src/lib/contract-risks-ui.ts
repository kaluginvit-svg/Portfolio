import type { AlertRow } from "@/components/common/alert-list";
import type { Contract, ContractRiskScanResult } from "@/types/finance";

function mapList(category: string, severity: string, items: Contract[]): AlertRow[] {
  return items.map((c) => ({
    alert_type: category,
    severity,
    message: `${c.contract_name ?? "—"} · ${c.counterparty ?? "—"}`,
    related_entity: `contract:${c.id}`,
    created_at: "",
  }));
}

export function flattenContractRisks(data: ContractRiskScanResult): AlertRow[] {
  return [
    ...mapList("expiring_soon", "medium", data.expiring_soon),
    ...mapList("missing_payment_terms", "low", data.missing_payment_terms),
    ...mapList("missing_penalty_terms", "low", data.missing_penalty_terms),
    ...mapList("missing_amount", "medium", data.missing_amount),
    ...mapList("no_end_date", "low", data.no_end_date),
    ...mapList("penalty_detected", "info", data.penalty_detected),
  ];
}
