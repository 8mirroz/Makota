"""Makota Industrial OS: Interactive End-to-End Demo Showcase CLI.

Демонстрирует работу всех 6 вычислительных модулей системы на реальных производственных
сценариях одной командой:
    python3 engine/demo_showcase.py
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.cost_calculator import CostEngineer
from engine.logistics_validator import LogisticsValidator
from engine.procurement_matcher import ProcurementMatcher, RawStockRequirement
from engine.quality_and_tooling import (
    DimensionMeasurement,
    QualityAndToolingEngine,
    ToolLifeRecord,
)
from engine.vault_runner import build_pilot_report


def generate_showcase_output(vault_dir: Path = _REPO_ROOT) -> str:
    lines: List[str] = [
        "================================================================================",
        "  MAKOTA INDUSTRIAL OS — ДЕМОНСТРАЦИЯ ВЫЧИСЛИТЕЛЬНОГО ЯДРА (6 МОДУЛЕЙ)",
        "================================================================================",
        "",
    ]

    # 1. Cost Engineer & RegionStroy Tender Case
    routes = CostEngineer.generate_three_routes(
        part_name="Фланец переходной D140 (ст. 40Х)",
        material="40Х",
        weight_kg=12.5,
        base_metal_price_per_kg=110.0,
        is_hollow_or_flange=True,
    )
    bid = CostEngineer.analyze_competitive_bid(
        batch_size=150,
        baseline_cost_rub=100000.0,
        baseline_quote_rub=137000.0,
        competitor_price_rub=100580.0,
        optimized_cost_rub=76800.0,
        target_margin_percent=0.22,
    )
    mob = CostEngineer.evaluate_make_or_buy(
        inhouse_route=routes[1],
        subcontract_route=routes[2],
        batch_size=150,
        available_machine_hours=45.0,
    )

    lines.extend(
        [
            "[1/6] AI COST ENGINEER & ТЕНДЕРНЫЙ АНАЛИЗ (Кейс «РегионСтрой»)",
            f"  • Сгенерировано маршрутов: {len(routes)} (A: Базовый, B: Оптимальный ЧПУ, C: Кооперация)",
            f"  • Старая себестоимость / Старое КП: {bid['baseline_cost_rub']:,.0f} ₽ / {bid['baseline_quote_rub']:,.0f} ₽ (Проигрыш)",
            f"  • Цена победителя (РегионСтрой):    {bid['competitor_price_rub']:,.0f} ₽",
            f"  • Новая себестоимость Makota:       {bid['optimized_cost_rub']:,.0f} ₽ (экономия {bid['savings_against_baseline_cost_rub']:,.0f} ₽)",
            f"  • Рекомендуемая победная цена:      {bid['recommended_winning_price_rub']:,.0f} ₽ (дельта к конкуренту: {bid['price_delta_to_competitor_rub']:,.0f} ₽)",
            f"  • Чистая прибыль завода со сделки:  +{bid['projected_margin_rub']:,.0f} ₽ (эффективная маржа {bid['effective_margin_percent']}%)",
            f"  • Анализ Make-or-Buy (150 шт):      требуется {mob['required_machine_hours']} станко-ч -> стратегия [{mob['recommendation']}]",
            "",
        ]
    )

    # 2. Procurement Matcher
    reqs = [
        RawStockRequirement("MKT-081", "Заказчик 1", "40Х", "круг", "150", 1200.0, "2026-11-20", 132000.0),
        RawStockRequirement("MKT-084", "ПАО «ТатНефтеМаш»", "40Х", "круг", "150", 1650.0, "2026-11-22", 181500.0),
        RawStockRequirement("MKT-085", "ООО «ВолгаСпецСтрой»", "12Х18Н10Т", "круг", "70", 1100.0, "2026-11-25", 440000.0),
    ]
    lots = ProcurementMatcher.consolidate_requirements(reqs)
    lines.append("[2/6] КОНСОЛИДАЦИЯ ОПТОВЫХ ПУЛОВ МЕТАЛЛОПРОКАТА (Procurement Pool)")
    for lot in lots:
        lines.append(
            f"  • Лот {lot.pool_id} ({lot.steel_grade}, {lot.profile_type} {lot.dimension_mm} мм): "
            f"{lot.total_weight_kg:,.0f} кг | Скидка -{lot.discount_percent}% | Прямая экономия: +{lot.savings_rub:,.0f} ₽ [{lot.status}]"
        )
    lines.append("")

    # 3. Logistics Validator
    log_res = LogisticsValidator.evaluate_rate(
        route_key="CHELYABINSK_ALMETYEVSK",
        requested_rate_rub=17000.0,
        cargo_weight_kg=1200.0,
        is_urgent=False,
    )
    lines.extend(
        [
            "[3/6] АУДИТ ТРАНСПОРТНЫХ СТАВОК ПО КОРИДОРАМ АТИ.СУ (Logistics Validator)",
            f"  • Маршрут: {log_res['route_name']} ({log_res['cargo_weight_kg']:,.0f} кг)",
            f"  • Запрошено логистом: {log_res['requested_rate_rub']:,.0f} ₽ vs Рынок АТИ.СУ (догруз): {log_res['benchmark_market_rate_rub']:,.0f} ₽",
            f"  • Выявлена переплата: +{log_res['overpay_percent']}% | Потенциал экономии: +{log_res['savings_potential_rub']:,.0f} ₽",
            "",
        ]
    )

    # 4 & 5. Vault Runner (Order Controller SLA + Dynamic CNC Production Planner)
    _, stats = build_pilot_report(vault_dir, now=datetime(2026, 11, 18, 12, 0))
    lines.extend(
        [
            "[4/6 & 5/6] ЦИФРОВОЙ БЕГУНОК (SLA) И АЛГОРИТМИЧЕСКОЕ РАСПИСАНИЕ ЧПУ (Obsidian Vault)",
            f"  • Прочитано карточек активных заказов из Vault: {stats['orders_count']} шт. на сумму {stats['total_revenue_rub']:,.0f} ₽",
            f"  • Плановая валовая маржа портфеля:              {stats['total_margin_rub']:,.0f} ₽",
            f"  • Выявлено реальных SLA-узких мест:             {stats['alerts_count']} (задержка поставки нержавейки MKT-2026-085)",
            f"  • Построено слотов расписания ЧПУ (правило EDD): {stats['scheduled_slots_count']} с учётом матрицы переналадок",
            "",
        ]
    )

    # 6. Quality Intelligence & Tool Wear Monitor
    tools = [
        ToolLifeRecord("T01", "T01", "проходной резец", "CNMG 120408-PM", 30.0, 18.0),
        ToolLifeRecord("T03", "T03", "чистовой резец", "DNMG 150604-PF", 25.0, 22.0),
        ToolLifeRecord("T11", "T11", "расточной резец", "CCMT 09T304", 25.0, 24.0),
    ]
    tool_statuses = QualityAndToolingEngine.audit_turret_magazine(tools)
    qc_res = QualityAndToolingEngine.evaluate_qc_measurements(
        protocol_id="QC-2026-084",
        order_id="MKT-2026-084",
        batch_size=150,
        unit_cost_rub=1633.0,
        measurement=DimensionMeasurement(
            feature="Посадочный диаметр D140H7",
            nominal_mm=140.0,
            upper_deviation_mm=0.040,
            lower_deviation_mm=0.000,
            measured_values_mm=[140.018, 140.020, 140.019, 140.022, 140.021],
        ),
    )

    lines.append("[6/6] КОНТРОЛЬ СТОЙКОСТИ ПЛАСТИН И ПРОТОКОЛ ОТК (Quality & Tooling)")
    for ts in tool_statuses:
        lines.append(
            f"  • Позиция {ts.turret_position} ({ts.insert_type}): износ {ts.wear_percent}% "
            f"(остаток {ts.remaining_life_min} мин) -> [{ts.risk_level}]"
        )
    lines.extend(
        [
            f"  • Протокол ОТК {qc_res['protocol_id']} ({qc_res['feature']}): вердикт [{qc_res['overall_verdict'].upper()}], индекс точности Cpk = {qc_res['cpk_index']}",
            "",
            "================================================================================",
            "  ВСЕ 6 ВЫЧИСЛИТЕЛЬНЫХ МОДУЛЕЙ ОТРАБОТАЛИ УСПЕШНО (0 внешних зависимостей)",
            "================================================================================",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    print(generate_showcase_output())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
