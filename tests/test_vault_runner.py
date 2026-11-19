"""Unit tests for Makota Vault Runner CLI and Vault Parser (engine/vault_runner.py, engine/vault_parser.py)."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from engine.order_sla_tracker import OrderSLATracker
from engine.vault_parser import (
     ORDERS_REL_DIR,
    resolve_stage_entered_at,
    validate_vault_order_frontmatter,
)
from engine.vault_runner import build_pilot_report, load_vault_orders, parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestVaultRunner(unittest.TestCase):
    def test_parses_frontmatter_from_md(self):
        order_path = (
            REPO_ROOT
            / "02_Продажи_и_Заказы"
            / "Активные_заказы"
            / "Заказ_MKT-084_Фланцы_40Х.md"
        )
        fm = parse_frontmatter(order_path.read_text(encoding="utf-8"))
        self.assertEqual(fm.get("type"), "order")
        self.assertEqual(fm.get("order_id"), "MKT-2026-084")
        self.assertEqual(fm.get("status"), "06_в_производстве")
        self.assertEqual(fm.get("material"), "40Х")
        self.assertEqual(validate_vault_order_frontmatter(fm), [])

        orders = load_vault_orders(REPO_ROOT, now=datetime(2026, 11, 18, 12, 0))
        self.assertGreaterEqual(len(orders), 3)
        ids = {o.order_id for o in orders}
        self.assertIn("MKT-2026-084", ids)

    def test_all_active_vault_orders_conform_to_contract(self):
        orders_dir = REPO_ROOT / ORDERS_REL_DIR
        for md_path in sorted(orders_dir.glob("*.md")):
            fm = parse_frontmatter(md_path.read_text(encoding="utf-8"))
            if fm.get("type") == "order":
                errors = validate_vault_order_frontmatter(fm)
                self.assertEqual(errors, [], f"Contract errors in {md_path.name}: {errors}")

    def test_stage_entered_at_priority_eliminates_false_sla_breach(self):
        ref_now = datetime(2026, 11, 18, 12, 0)
        orders = {o.order_id: o for o in load_vault_orders(REPO_ROOT, now=ref_now)}

        # MKT-2026-084 находится в цеху ЧПУ с 17.11 09:00 (27 ч из 72 ч норматива -> OK)
        mkt_084 = orders["MKT-2026-084"]
        sla_084 = OrderSLATracker.evaluate_order_status(
            order_id=mkt_084.order_id,
            client=mkt_084.client,
            current_stage=mkt_084.status,
            entered_stage_at=mkt_084.entered_stage_at,
            now=ref_now,
        )
        self.assertFalse(sla_084.is_breached)
        self.assertEqual(sla_084.risk_level, "OK")

        # MKT-2026-085 ожидает поставку нержавейки с 16.11 09:00 (51 ч из 24 ч норматива -> CRITICAL)
        mkt_085 = orders["MKT-2026-085"]
        sla_085 = OrderSLATracker.evaluate_order_status(
            order_id=mkt_085.order_id,
            client=mkt_085.client,
            current_stage=mkt_085.status,
            entered_stage_at=mkt_085.entered_stage_at,
            now=ref_now,
        )
        self.assertTrue(sla_085.is_breached)
        self.assertEqual(sla_085.risk_level, "CRITICAL")

        # Проверка приоритета полей: stage_entered_at > updated_at > created_at
        sample_fm = {
            "created_at": "2026-11-01",
            "updated_at": "2026-11-10",
            "stage_entered_at": "2026-11-18T10:30:00",
        }
        resolved = resolve_stage_entered_at(sample_fm, ref_now)
        self.assertEqual(resolved, datetime(2026, 11, 18, 10, 30, 0))

    def test_generates_report_with_all_sections(self):
        report_md, stats = build_pilot_report(
            REPO_ROOT, now=datetime(2026, 11, 18, 12, 0)
        )
        self.assertGreaterEqual(stats["orders_count"], 3)
        self.assertEqual(stats["alerts_count"], 1)  # Только реальный срыв поставки по MKT-2026-085
        for heading in (
            "## Сводка портфеля",
            "## SLA-алерты",
            "## Пулы закупок металла",
            "## Расписание загрузки ЧПУ (Dynamic Scheduling)",
            "## Итог",
        ):
            self.assertIn(heading, report_md)

    def test_no_orders_gives_empty_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_md, stats = build_pilot_report(
                Path(tmp_dir), now=datetime(2026, 11, 18, 12, 0)
            )
            self.assertEqual(stats["orders_count"], 0)
            self.assertEqual(stats["alerts_count"], 0)
            self.assertIn("## Сводка портфеля", report_md)
            self.assertIn("## Итог", report_md)


if __name__ == "__main__":
    unittest.main()
