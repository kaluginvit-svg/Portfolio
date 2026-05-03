"""Idempotent seed data for demos and tests."""

from __future__ import annotations

import json
import logging

from db import get_connection
from utils.helpers import utc_now_iso

logger = logging.getLogger(__name__)


def seed_if_empty() -> bool:
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM companies")
        if cur.fetchone()[0] > 0:
            logger.info("Seed skipped: companies already present.")
            return False

    _run_seed()
    logger.info("Seed data loaded.")
    return True


def _run_seed() -> None:
    created = utc_now_iso()
    months = [f"2024-{m:02d}-01" for m in range(1, 13)]

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO companies (name, currency, created_at) VALUES (?, ?, ?)",
            ("Demo Holdings OÜ", "EUR", created),
        )
        conn.execute(
            "INSERT INTO companies (name, currency, created_at) VALUES (?, ?, ?)",
            ("Subsidiary LLC", "USD", created),
        )
        conn.commit()

        c1 = conn.execute("SELECT id FROM companies WHERE name = ?", ("Demo Holdings OÜ",)).fetchone()[0]
        c2 = conn.execute("SELECT id FROM companies WHERE name = ?", ("Subsidiary LLC",)).fetchone()[0]

        # --- P&L Demo Holdings (monthly) ---
        base_rev = 850_000.0
        for i, d in enumerate(months):
            rev = base_rev + i * 12_000
            cogs = rev * 0.42
            opex = 210_000 + (i % 3) * 8_000
            ebitda = rev - cogs - opex
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'pnl', 'Revenue', 'Product sales', ?, 'EUR', 'seed', ?)""",
                (c1, d, rev, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'pnl', 'COGS', 'Materials', ?, 'EUR', 'seed', ?)""",
                (c1, d, -cogs, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'pnl', 'OPEX', 'SG&A', ?, 'EUR', 'seed', ?)""",
                (c1, d, -opex, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'pnl', 'EBITDA', 'Adjusted', ?, 'EUR', 'seed', ?)""",
                (c1, d, ebitda, created),
            )

        # --- Cash flow Demo Holdings ---
        for i, d in enumerate(months):
            op_cf = 180_000 + i * 5_000
            inv_cf = -35_000 if i % 4 == 0 else -12_000
            fin_cf = -25_000
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, department, amount, currency, source_file, created_at)
                VALUES (?, ?, 'cashflow', 'Operating', 'Treasury', ?, 'EUR', 'seed', ?)""",
                (c1, d, op_cf, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, department, amount, currency, source_file, created_at)
                VALUES (?, ?, 'cashflow', 'Investing', 'Capex', ?, 'EUR', 'seed', ?)""",
                (c1, d, inv_cf, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, department, amount, currency, source_file, created_at)
                VALUES (?, ?, 'cashflow', 'Financing', 'Debt service', ?, 'EUR', 'seed', ?)""",
                (c1, d, fin_cf, created),
            )

        # --- Balance (month-end snapshots, simplified) ---
        for i, d in enumerate(months):
            assets = 2_400_000 + i * 45_000
            liab = 980_000 + i * 20_000
            equity = assets - liab
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'balance', 'Assets', 'Total', ?, 'EUR', 'seed', ?)""",
                (c1, d, assets, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'balance', 'Liabilities', 'Total', ?, 'EUR', 'seed', ?)""",
                (c1, d, -liab, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, subcategory, amount, currency, source_file, created_at)
                VALUES (?, ?, 'balance', 'Equity', 'Total', ?, 'EUR', 'seed', ?)""",
                (c1, d, equity, created),
            )

        # --- AR / AP ---
        partners = ["Acme Retail", "Northwind Traders", "Contoso GmbH", "Fabrikam AS"]
        for i, d in enumerate(months):
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, counterparty, amount, currency, source_file, created_at)
                VALUES (?, ?, 'ar', 'Trade AR', ?, ?, 'EUR', 'seed', ?)""",
                (c1, d, partners[i % len(partners)], 120_000 + i * 3_200, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, counterparty, amount, currency, source_file, created_at)
                VALUES (?, ?, 'ap', 'Trade AP', ?, ?, 'EUR', 'seed', ?)""",
                (c1, d, partners[(i + 1) % len(partners)], -(88_000 + i * 2_100), created),
            )

        # --- Payments calendar (scheduled) ---
        pay_days = [
            ("2024-06-05", "Vendor services", -42_000),
            ("2024-06-18", "Payroll", -185_000),
            ("2024-07-02", "Lease", -28_000),
            ("2024-07-22", "Customer receipt", 95_000),
            ("2024-08-10", "Tax payment", -62_000),
            ("2024-08-30", "Supplier", -33_500),
            ("2024-09-12", "Customer receipt", 110_000),
            ("2024-10-01", "Insurance", -9_800),
        ]
        for pd, desc, amt in pay_days:
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, project, amount, currency, source_file, created_at)
                VALUES (?, ?, 'payments', ?, 'Scheduled', ?, 'EUR', 'seed', ?)""",
                (c1, pd, desc, amt, created),
            )

        # --- Subsidiary LLC simplified P&L + payments (USD) ---
        for i, d in enumerate(months[:6]):
            rev = 410_000 + i * 7_000
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, region, amount, currency, source_file, created_at)
                VALUES (?, ?, 'pnl', 'Revenue', 'US-East', ?, 'USD', 'seed', ?)""",
                (c2, d, rev, created),
            )
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, region, amount, currency, source_file, created_at)
                VALUES (?, ?, 'pnl', 'OPEX', 'US-East', ?, 'USD', 'seed', ?)""",
                (c2, d, -(rev * 0.35 + 95_000), created),
            )

        # --- Cash positions (latest month-end style) ---
        banks = [
            ("EE12 3456 7890 0011", "Swedbank", 420_000),
            ("EE98 7654 3210 0099", "LHV", 128_500),
        ]
        for acc, bnk, bal in banks:
            conn.execute(
                """INSERT INTO cash_positions
                (company_id, position_date, bank_account, bank_name, amount, currency, source_file, created_at)
                VALUES (?, '2024-12-31', ?, ?, ?, 'EUR', 'seed', ?)""",
                (c1, acc, bnk, bal, created),
            )
        conn.execute(
            """INSERT INTO cash_positions
            (company_id, position_date, bank_account, bank_name, amount, currency, source_file, created_at)
            VALUES (?, '2024-12-31', 'US-CHASE-7781', 'Chase', 215000, 'USD', 'seed', ?)""",
            (c2, created),
        )

        # --- Budget (slightly lower revenue vs fact for variance demo) ---
        for i, d in enumerate(months):
            plan_rev = base_rev + i * 10_000
            plan_opex = 215_000 + (i % 3) * 7_500
            conn.execute(
                """INSERT INTO budget_records
                (company_id, record_date, statement_type, category, department, amount, currency, version, source_file, created_at)
                VALUES (?, ?, 'budget', 'Revenue', 'FP&A', ?, 'EUR', 'v2024.1', 'seed', ?)""",
                (c1, d, plan_rev, created),
            )
            conn.execute(
                """INSERT INTO budget_records
                (company_id, record_date, statement_type, category, department, amount, currency, version, source_file, created_at)
                VALUES (?, ?, 'budget', 'OPEX', 'FP&A', ?, 'EUR', 'v2024.1', 'seed', ?)""",
                (c1, d, -plan_opex, created),
            )

        # --- KPI rows (optional explicit KPI statement) ---
        for i, d in enumerate(months[-3:]):
            conn.execute(
                """INSERT INTO financial_records
                (company_id, record_date, statement_type, category, product, amount, currency, source_file, created_at)
                VALUES (?, ?, 'kpi', 'Net retention', 'NRR_pct', ?, 'EUR', 'seed', ?)""",
                (c1, d, 108.5 + i * 0.4, created),
            )

        # --- Contracts ---
        contracts = [
            (
                "MSA-2023-CloudOps",
                "CloudOps Oy",
                "2023-01-15",
                "2025-12-31",
                "Net 30 from invoice",
                "0.05% daily late fee after 45 days",
                "EUR",
                240_000,
                "Payment due within 30 days. Penalty 0.05% daily after 45 days.",
            ),
            (
                "Lease-Baltic-Hub",
                "Baltic RE Fund",
                "2022-06-01",
                "2027-05-31",
                "Quarterly in advance",
                None,
                "EUR",
                360_000,
                "Quarterly rent. No explicit penalty clause.",
            ),
            (
                "Support-Northwind",
                "Northwind Traders",
                "2024-03-01",
                None,
                None,
                None,
                "USD",
                None,
                "Rolling support agreement. End date TBD.",
            ),
            (
                "Data-Processing-DPA",
                "Contoso GmbH",
                "2024-01-10",
                "2026-01-09",
                "Annual upfront",
                "Termination for breach with 30d cure",
                "EUR",
                85_000,
                "Annual license. Penalty on breach per statutory damages.",
            ),
            (
                "Short-Marketing",
                "Fabrikam AS",
                "2025-02-01",
                "2025-04-30",
                "Net 14",
                "",
                "EUR",
                22_000,
                "Campaign ending April 2025. Payment terms Net 14.",
            ),
            (
                "Logistics-Frame",
                "Frame Logistics",
                "2021-11-01",
                "2024-10-31",
                "Net 45",
                "2% per month overdue",
                "EUR",
                150_000,
                "Late payment interest 2% monthly.",
            ),
            (
                "IT-Hardware",
                "Initech Supply",
                "2024-08-15",
                "2025-08-14",
                "50/50 milestone",
                None,
                "EUR",
                95_000,
                "50% on order, 50% on delivery.",
            ),
        ]
        for row in contracts:
            conn.execute(
                """INSERT INTO contracts
                (contract_name, counterparty, start_date, end_date, payment_terms, penalty_terms, currency, amount, source_file, raw_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'seed', ?, ?)""",
                (*row, created),
            )

        # --- Investment projects ---
        scenarios = [
            (
                "Warehouse automation",
                c1,
                1_200_000,
                10.0,
                12.0,
                "EUR",
                json.dumps({"cash_flows": [320_000, 340_000, 360_000, 380_000, 400_000]}),
                "5-year ops savings program",
            ),
            (
                "SaaS platform rebuild",
                c1,
                2_500_000,
                11.5,
                14.0,
                "EUR",
                json.dumps({"cash_flows": [450_000, 520_000, 610_000, 700_000, 780_000, 820_000]}),
                "Phased rollout",
            ),
            (
                "US market entry",
                c2,
                800_000,
                12.0,
                15.0,
                "USD",
                json.dumps({"cash_flows": [0, 180_000, 260_000, 340_000, 410_000]}),
                "Includes ramp-up year",
            ),
            (
                "Solar rooftop pilot",
                c1,
                450_000,
                8.0,
                9.0,
                "EUR",
                json.dumps({"cash_flows": [95_000, 102_000, 108_000, 115_000, 120_000, 125_000]}),
                "Energy savings + incentives",
            ),
        ]
        for row in scenarios:
            conn.execute(
                """INSERT INTO investment_projects
                (project_name, company_id, initial_investment, discount_rate, hurdle_rate, currency, scenario_json, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (*row, created),
            )

        # --- Mappings sample ---
        conn.execute(
            "INSERT INTO mappings (source_value, target_type, target_value, created_at) VALUES (?, ?, ?, ?)",
            ("SG&A", "category", "OPEX", created),
        )
        conn.execute(
            "INSERT INTO mappings (source_value, target_type, target_value, created_at) VALUES (?, ?, ?, ?)",
            ("GME", "category", "COGS", created),
        )

        conn.commit()
