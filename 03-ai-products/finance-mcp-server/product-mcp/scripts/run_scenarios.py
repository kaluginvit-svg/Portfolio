#!/usr/bin/env python3
"""
Scenario harness: sequential integration checks + JSON report.

Run from product-mcp root:
  python scripts/run_scenarios.py

Report: test_reports/scenario_report.json
"""

from __future__ import annotations

import json
import shutil
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    root = _root()
    import os
    import sys

    sys.path.insert(0, str(root))
    os.chdir(root)

    reports_dir = root / "test_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "scenario_report.json"

    scenarios: list[dict] = []
    passed = 0
    failed = 0

    def run(name: str, fn) -> None:
        nonlocal passed, failed
        detail = ""
        err: str | None = None
        tb: str | None = None
        try:
            fn()
            detail = "ok"
            passed += 1
            scenarios.append({"name": name, "status": "passed", "details": detail, "error": None, "traceback": None})
        except Exception as e:
            err = str(e)
            tb = traceback.format_exc()
            failed += 1
            scenarios.append({"name": name, "status": "failed", "details": detail, "error": err, "traceback": tb})
            print(f"[FAIL] {name}: {err}")

    fixtures = root / "tests" / "fixtures"

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        from tests.support.bootstrap import full_bootstrap

        ctx = full_bootstrap(base, "scenario_mcp.db")
        d = ctx["dispatch"]

        company = d("list_companies", {})["result"]["companies"][0]["name"]

        def startup_and_seed() -> None:
            h = d("health_check", {})
            assert h["success"] and h["result"]["counts_by_table"]["companies"] >= 1

        def registry_integrity() -> None:
            import registry
            from schemas import tool_bundles

            assert set(registry.list_tool_names()) == {b.name for b in tool_bundles()}

        def import_pnl_csv() -> None:
            dst = base / "sc_pnl.csv"
            shutil.copy(fixtures / "sample_pnl.csv", dst)
            r = d(
                "import_csv",
                {"file_path": str(dst), "statement_type": "pnl", "company_name": company},
            )
            assert r["success"] and r["result"]["imported_count"] > 0

        def import_budget_csv() -> None:
            dst = base / "sc_budget.csv"
            shutil.copy(fixtures / "sample_budget.csv", dst)
            r = d(
                "import_csv",
                {
                    "file_path": str(dst),
                    "statement_type": "budget",
                    "company_name": company,
                    "version": "scenario-v1",
                },
            )
            assert r["success"] and r["result"]["imported_count"] > 0

        def calculate_kpis() -> None:
            r = d(
                "calculate_kpis",
                {
                    "company_name": company,
                    "period_start": "2024-01-01",
                    "period_end": "2024-12-31",
                },
            )
            assert r["success"] and isinstance(r["result"]["total_revenue"], (int, float))

        def plan_vs_fact() -> None:
            r = d(
                "plan_vs_fact",
                {
                    "company_name": company,
                    "period_start": "2024-01-01",
                    "period_end": "2024-12-31",
                },
            )
            assert r["success"] and len(r["result"]["breakdown_by_category"]) >= 1

        def liquidity_forecast() -> None:
            r = d("liquidity_forecast", {"company_name": company, "days": 14})
            assert r["success"] and len(r["result"]["daily_projection"]) == 14

        def import_contract_and_scan_risks() -> None:
            dst = base / "sc_contract.txt"
            shutil.copy(fixtures / "sample_contract.txt", dst)
            imp = d("import_contract", {"file_path": str(dst)})
            assert imp["success"] and imp["result"].get("contract_id")
            scan = d("contract_risk_scan", {})
            assert scan["success"] and "alerts_created" in scan["result"]

        def add_and_evaluate_investment() -> None:
            import json as _json

            r = d(
                "add_investment_project",
                {
                    "project_name": "Scenario Project",
                    "company_name": company,
                    "initial_investment": 100_000,
                    "discount_rate": 10.0,
                    "hurdle_rate": 11.0,
                    "scenario_json": _json.dumps({"cash_flows": [40_000, 40_000, 40_000]}),
                    "notes": "scenario",
                },
            )
            assert r["success"] and r["result"].get("id")
            pid = r["result"]["id"]
            ev = d("evaluate_investment", {"project_id": pid})
            assert ev["success"] and ev["result"].get("recommendation")

        def safe_calc_negative_case() -> None:
            r = d("calculate", {"expression": '__import__("os")'})
            assert r["success"] and r["result"]["error"]

        def export_report() -> None:
            r = d(
                "export_report",
                {
                    "report_type": "kpis",
                    "output_format": "json",
                    "company_name": company,
                    "period_start": "2024-01-01",
                    "period_end": "2024-12-31",
                },
            )
            assert r["success"] and r["result"].get("path")
            assert Path(r["result"]["path"]).is_file()

        for name, fn in [
            ("startup_and_seed", startup_and_seed),
            ("registry_integrity", registry_integrity),
            ("import_pnl_csv", import_pnl_csv),
            ("import_budget_csv", import_budget_csv),
            ("calculate_kpis", calculate_kpis),
            ("plan_vs_fact", plan_vs_fact),
            ("liquidity_forecast", liquidity_forecast),
            ("import_contract_and_scan_risks", import_contract_and_scan_risks),
            ("add_and_evaluate_investment", add_and_evaluate_investment),
            ("safe_calc_negative_case", safe_calc_negative_case),
            ("export_report", export_report),
        ]:
            print(f"[RUN] {name}")
            run(name, fn)

    report = {
        "timestamp": _iso(),
        "project": "product-mcp",
        "summary": {"total": passed + failed, "passed": passed, "failed": failed},
        "scenarios": scenarios,
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to {out_path}")
    print(json.dumps(report["summary"], indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
