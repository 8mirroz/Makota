"""Unit tests for Makota Industrial OS Engine algorithms."""

import unittest
from datetime import datetime, timedelta

from engine.cost_calculator import CostEngineer, ManufacturingRoute, MachiningOperation
from engine.procurement_matcher import ProcurementMatcher, RawStockRequirement
from engine.logistics_validator import LogisticsValidator
from engine.order_sla_tracker import OrderSLATracker


class TestMakotaEngine(unittest.TestCase):
    def test_cost_engineer_three_routes_and_calculation(self):
        routes = CostEngineer.generate_three_routes(
            part_name="Фланец переходной D140",
            material="40Х",
            weight_kg=12.5,
            base_metal_price_per_kg=110.0,
            is_hollow_or_flange=True,
        )
        self.assertEqual(len(routes), 3)

        # Проверяем расчет стоимости партии 150 шт
        batch_size = 150
        baseline_cost = routes[0].calculate_cost(batch_size)
        optimized_cost = routes[1].calculate_cost(batch_size)
        subcontract_cost = routes[2].calculate_cost(batch_size)

        self.assertGreater(baseline_cost["total_cost_rub"], optimized_cost["total_cost_rub"])
        self.assertGreater(baseline_cost["total_material_rub"], optimized_cost["total_material_rub"])

    def test_competitive_bid_analysis_regionstroy_case(self):
        """Проверка победы над конкурентом РегионСтрой (100 580 руб vs наши 137 000 руб)."""
        analysis = CostEngineer.analyze_competitive_bid(
            batch_size=1,
            baseline_cost_rub=100000.0,       # 82к с/с + 17к логистика = ~100к
            baseline_quote_rub=137000.0,      # Наша старая проигрышная цена
            competitor_price_rub=100580.0,    # Цена победителя РегионСтрой
            optimized_cost_rub=76800.0,       # Новая себестоимость после пула и инструмента
            target_margin_percent=0.22,       # Целевая маржа 22%
        )

        self.assertTrue(analysis["beats_competitor"])
        self.assertLess(analysis["recommended_winning_price_rub"], 100580.0)
        self.assertGreater(analysis["projected_margin_rub"], 15000.0)
        self.assertIn("ПОБЕДА В ТЕНДЕРЕ", analysis["verdict"])

    def test_procurement_pool_aggregation_and_discounts(self):
        reqs = [
            RawStockRequirement("MKT-081", "Заказчик 1", "40Х", "круг", "150", 1200.0, "2026-11-20", 132000.0),
            RawStockRequirement("MKT-084", "ТатНефтеМаш", "40Х", "круг", "150", 1650.0, "2026-11-22", 181500.0),
            RawStockRequirement("MKT-085", "Клиент 2", "12Х18Н10Т", "круг", "70", 850.0, "2026-11-25", 340000.0),
        ]

        lots = ProcurementMatcher.consolidate_requirements(reqs)
        self.assertEqual(len(lots), 2)  # 40Х и 12Х18Н10Т

        lot_40x = [l for l in lots if l.steel_grade == "40Х"][0]
        self.assertEqual(lot_40x.total_weight_kg, 2850.0)
        self.assertEqual(lot_40x.discount_percent, 10.0)  # Свыше 2 тонн -> 10%
        self.assertGreater(lot_40x.savings_rub, 30000.0)

    def test_logistics_validator_detects_inflated_rate(self):
        # Логист запросил 17 000 руб за доставку Челябинск - Альметьевск
        result = LogisticsValidator.evaluate_rate(
            route_key="CHELYABINSK_ALMETYEVSK",
            requested_rate_rub=17000.0,
            cargo_weight_kg=1200.0,
            is_urgent=False,
        )

        self.assertTrue(result["is_inflated"])
        self.assertEqual(result["benchmark_market_rate_rub"], 8500.0)
        self.assertEqual(result["savings_potential_rub"], 8500.0)

    def test_order_sla_tracker_critical_alert(self):
        now = datetime(2026, 11, 14, 12, 0, 0)
        # Заказ завис в закупках на 50 часов при нормативе 24 часа
        stuck_time = now - timedelta(hours=50)

        status = OrderSLATracker.evaluate_order_status(
            order_id="MKT-084",
            client="ТатНефтеМаш",
            current_stage="03_metal_procurement",
            entered_stage_at=stuck_time,
            now=now,
        )

        self.assertTrue(status.is_breached)
        self.assertEqual(status.risk_level, "CRITICAL")
        self.assertIn("КРИТИЧЕСКИЙ СРЫВ SLA", status.alert_message)


if __name__ == "__main__":
    unittest.main()
