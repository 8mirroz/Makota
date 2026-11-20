"""Unit tests for Makota Industrial OS Engine algorithms and JSON Schema contracts."""

import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from engine.cost_calculator import CostEngineer, ManufacturingRoute, MachiningOperation
from engine.demo_showcase import generate_showcase_output
from engine.logistics_validator import LogisticsValidator
from engine.order_sla_tracker import OrderSLATracker
from engine.procurement_matcher import ProcurementMatcher, RawStockRequirement
from engine.production_planner import ProductionJob, ProductionPlanner
from engine.quality_and_tooling import (
    DimensionMeasurement,
    QualityAndToolingEngine,
    ToolLifeRecord,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


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
        self.assertGreater(subcontract_cost["total_cost_rub"], 0.0)

    def test_make_or_buy_indifference_and_capacity_split(self):
        # Собственное ЧПУ: высокая стоимость наладки/логистики, но низкая себестоимость детали
        inhouse = ManufacturingRoute(
            route_id="ROUTE-INHOUSE",
            description="Собственное ЧПУ с высокой наладкой",
            raw_material_cost_rub=500.0,
            waste_coefficient=1.2,
            operations=[
                MachiningOperation("Наладка и обработка ЧПУ", "CNC-LATHE-01", 180.0, 12.0, 2500.0, 100.0)
            ],
            logistics_cost_rub=8500.0,
            overhead_percent=0.15,
        )
        # Полный внешний субподряд: минимальные фиксированные затраты, но выше цена за штуку
        subcontract = ManufacturingRoute(
            route_id="ROUTE-SUBCONTRACT",
            description="Полный субподряд под ключ",
            raw_material_cost_rub=0.0,
            waste_coefficient=1.0,
            operations=[],
            subcontract_cost_rub=1550.0,
            logistics_cost_rub=3000.0,
            overhead_percent=0.10,
        )

        # На малой партии (10 шт < N*) выгоднее отдать на субподряд
        res_small = CostEngineer.evaluate_make_or_buy(
            inhouse_route=inhouse,
            subcontract_route=subcontract,
            batch_size=10,
            available_machine_hours=100.0,
        )
        self.assertEqual(res_small["recommendation"], "BUY_SUBCONTRACT")
        self.assertIsNotNone(res_small["indifference_batch_size"])
        self.assertGreater(res_small["indifference_batch_size"], 10.0)

        # На крупной партии (150 шт > N*) при свободном парке станков выгоднее свое ЧПУ
        res_free = CostEngineer.evaluate_make_or_buy(
            inhouse_route=inhouse,
            subcontract_route=subcontract,
            batch_size=150,
            available_machine_hours=100.0,
        )
        self.assertEqual(res_free["recommendation"], "MAKE_IN_HOUSE")
        self.assertFalse(res_free["capacity_constrained"])
        self.assertLess(res_free["indifference_batch_size"], 150.0)
        self.assertGreater(res_free["savings_rub"], 0.0)

        # При дефиците станочного времени на крупной партии рекомендуется гибридное разделение
        res_constrained = CostEngineer.evaluate_make_or_buy(
            inhouse_route=inhouse,
            subcontract_route=subcontract,
            batch_size=150,
            available_machine_hours=10.0,
        )
        self.assertTrue(res_constrained["capacity_constrained"])
        self.assertEqual(res_constrained["recommendation"], "HYBRID_SPLIT")

    def test_competitive_bid_analysis_tender_simulation(self):
        """Проверка расчёта целевой победной цены ниже ориентира рынка при сохранении целевой маржи."""
        analysis = CostEngineer.analyze_competitive_bid(
            batch_size=1,
            baseline_cost_rub=100000.0,       # Базовая расчётная с/с с логистикой
            baseline_quote_rub=137000.0,      # Базовое КП до оптимизации
            competitor_price_rub=100580.0,    # Целевой проходной ориентир тендера
            optimized_cost_rub=76800.0,       # Оптимизированная с/с после пула и маршрута
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

    def test_procurement_pool_temporal_window_splitting(self):
        reqs = [
            RawStockRequirement("MKT-081", "Клиент А", "40Х", "круг", "150", 1100.0, "2026-11-20", 121000.0),
            RawStockRequirement("MKT-099", "Клиент Б", "40Х", "круг", "150", 1200.0, "2026-12-25", 132000.0),
        ]
        lots = ProcurementMatcher.consolidate_requirements(reqs, max_date_delta_days=10)
        self.assertEqual(len(lots), 2)
        pool_ids = {l.pool_id for l in lots}
        self.assertIn("POOL-40Х-150", pool_ids)
        self.assertIn("POOL-40Х-150-W2", pool_ids)

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

    def test_order_sla_tracker_critical_alert_and_terminal_stages(self):
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

        # Завершённый заказ не должен генерировать SLA-алертов даже спустя 200 часов
        closed_status = OrderSLATracker.evaluate_order_status(
            order_id="MKT-070",
            client="Архивный клиент",
            current_stage="09_закрыт_прибыль_зафиксирована",
            entered_stage_at=now - timedelta(hours=200),
            now=now,
        )
        self.assertFalse(closed_status.is_breached)
        self.assertEqual(closed_status.risk_level, "OK")
        self.assertIsNone(closed_status.alert_message)

    def test_production_planner_edd_and_changeover_setup(self):
        start_at = datetime(2026, 11, 18, 8, 0, 0)
        jobs = [
            ProductionJob("MKT-086", "Втулка БрАЖ", "БрАЖ9-4", 80, "2026-11-28", "CNC-LATHE-01", 10.0),
            ProductionJob("MKT-084", "Фланец D140", "40Х", 150, "2026-11-20", "CNC-LATHE-01", 12.0, "Срочный"),
            ProductionJob("MKT-085", "Шайба М36", "12Х18Н10Т", 400, "2026-11-25", "CNC-LATHE-01", 6.0),
        ]
        slots = ProductionPlanner.schedule_jobs(jobs, start_at=start_at)
        self.assertEqual(len(slots), 3)
        # По EDD первым должен идти MKT-084 (дедлайн 20.11), затем MKT-085 (25.11), затем MKT-086 (28.11)
        self.assertEqual([s.order_id for s in slots], ["MKT-084", "MKT-085", "MKT-086"])
        # Первая партия без переналадки, вторая (40Х -> 12Х18Н10Т) = 45 мин, третья (12Х18Н10Т -> БрАЖ) = 40 мин
        self.assertEqual(slots[0].setup_time_min, 0.0)
        self.assertEqual(slots[1].setup_time_min, 45.0)
        self.assertEqual(slots[2].setup_time_min, 40.0)

        gantt_md = ProductionPlanner.format_gantt_markdown(slots)
        self.assertIn("MKT-084", gantt_md)
        self.assertIn("45 мин", gantt_md)

    def test_json_schemas_and_agent_configs_validity(self):
        schema_files = [
            "specs/schemas/digital_thread_order.schema.json",
            "specs/schemas/machine_telemetry.schema.json",
            "specs/schemas/tool_registry.schema.json",
            "specs/schemas/qc_protocol.schema.json",
        ]
        try:
            import jsonschema
        except ImportError:
            jsonschema = None

        for rel_path in schema_files:
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Missing schema file: {rel_path}")
            schema = json.loads(full_path.read_text(encoding="utf-8"))
            self.assertEqual(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema.get("type"), "object")
            self.assertIn("properties", schema)
            self.assertIn("required", schema)
            if jsonschema is not None:
                jsonschema.Draft202012Validator.check_schema(schema)

        agent_configs = [
            "specs/agents/cost_engineer_agent_config.json",
            "specs/agents/order_controller_agent_config.json",
            "specs/agents/procurement_and_logistics_agent_config.json",
            "specs/agents/planner_setup_matrix.json",
        ]
        for rel_path in agent_configs:
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Missing agent config: {rel_path}")
            data = json.loads(full_path.read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict)

    def test_quality_and_tooling_wear_and_cpk(self):
        tools = [
            ToolLifeRecord("T01", "T01", "проходной резец", "CNMG 120408", 30.0, 15.0),
            ToolLifeRecord("T03", "T03", "чистовой резец", "DNMG 150604", 25.0, 22.0),
            ToolLifeRecord("T11", "T11", "расточной резец", "CCMT 09T304", 25.0, 24.5),
        ]
        statuses = QualityAndToolingEngine.audit_turret_magazine(tools)
        self.assertEqual([s.risk_level for s in statuses], ["OK", "WARNING", "CRITICAL"])

        # В допуске с высоким Cpk
        qc_good = QualityAndToolingEngine.evaluate_qc_measurements(
            protocol_id="QC-2026-084",
            order_id="MKT-2026-084",
            batch_size=150,
            unit_cost_rub=1633.0,
            measurement=DimensionMeasurement(
                feature="Посадка D80H7",
                nominal_mm=80.0,
                upper_deviation_mm=0.030,
                lower_deviation_mm=0.000,
                measured_values_mm=[80.014, 80.015, 80.016, 80.015, 80.015],
            ),
        )
        self.assertEqual(qc_good["overall_verdict"], "годен")
        self.assertEqual(qc_good["scrap_count"], 0)
        self.assertGreaterEqual(qc_good["cpk_index"], 1.33)

        # Выход за поле допуска -> расчёт стоимости брака
        qc_bad = QualityAndToolingEngine.evaluate_qc_measurements(
            protocol_id="QC-2026-084-ERR",
            order_id="MKT-2026-084",
            batch_size=150,
            unit_cost_rub=1600.0,
            measurement=DimensionMeasurement(
                feature="Посадка D80H7",
                nominal_mm=80.0,
                upper_deviation_mm=0.030,
                lower_deviation_mm=0.000,
                measured_values_mm=[80.015, 80.042, 79.990],
            ),
        )
        self.assertEqual(qc_bad["overall_verdict"], "условно годен")
        self.assertEqual(qc_bad["scrap_count"], 2)
        self.assertEqual(qc_bad["scrap_cost_rub"], 3200.0)

    def test_demo_showcase_runs_all_six_modules(self):
        output = generate_showcase_output(REPO_ROOT)
        for marker in (
            "[1/6] AI COST ENGINEER",
            "[2/6] КОНСОЛИДАЦИЯ ОПТОВЫХ ПУЛОВ",
            "[3/6] АУДИТ ТРАНСПОРТНЫХ СТАВОК",
            "[4/6 & 5/6] ЦИФРОВОЙ БЕГУНОК",
            "[6/6] КОНТРОЛЬ СТОЙКОСТИ ПЛАСТИН",
            "ВСЕ 6 ВЫЧИСЛИТЕЛЬНЫХ МОДУЛЕЙ ОТРАБОТАЛИ УСПЕШНО",
        ):
            self.assertIn(marker, output)
            self.assertTrue((REPO_ROOT / "PRESENTATION.md").exists())
            self.assertTrue((REPO_ROOT / "ONBOARDING.md").exists())


if __name__ == "__main__":
    unittest.main()
