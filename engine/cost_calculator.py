"""Makota Industrial OS: Cost Engineer & RFP Calculation Engine.

Implements full manufacturing cost breakdown (ISO 23247), 3-route generative
optimization, and competitive bidding analysis (RegionStroy benchmark).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MachiningOperation:
    name: str
    machine_type: str
    setup_time_min: float
    machining_time_min: float
    hourly_rate_rub: float
    tooling_wear_rub: float


@dataclass
class ManufacturingRoute:
    route_id: str
    description: str
    raw_material_cost_rub: float
    waste_coefficient: float
    operations: List[MachiningOperation]
    subcontract_cost_rub: float = 0.0
    logistics_cost_rub: float = 0.0
    overhead_percent: float = 0.15

    def calculate_cost(self, batch_size: int) -> Dict[str, float]:
        """Calculates total and unit cost for the given batch size."""
        if batch_size <= 0:
            raise ValueError("Размер партии должен быть больше 0")

        # Сырье с учетом коэффициента отхода в стружку
        total_material = self.raw_material_cost_rub * self.waste_coefficient * batch_size

        total_machining = 0.0
        total_setup = 0.0
        total_tooling = 0.0

        for op in self.operations:
            # Машинное время на всю партию
            mach_hours = (op.machining_time_min * batch_size) / 60.0
            total_machining += mach_hours * op.hourly_rate_rub

            # Переналадка (один раз на партию)
            setup_hours = op.setup_time_min / 60.0
            total_setup += setup_hours * op.hourly_rate_rub

            # Износ инструмента на партию
            total_tooling += op.tooling_wear_rub * batch_size

        direct_cost = (
            total_material
            + total_machining
            + total_setup
            + total_tooling
            + (self.subcontract_cost_rub * batch_size)
            + self.logistics_cost_rub
        )

        overhead = direct_cost * self.overhead_percent
        total_cost = direct_cost + overhead
        unit_cost = total_cost / batch_size

        return {
            "total_material_rub": round(total_material, 2),
            "total_machining_rub": round(total_machining, 2),
            "total_setup_rub": round(total_setup, 2),
            "total_tooling_rub": round(total_tooling, 2),
            "subcontract_total_rub": round(self.subcontract_cost_rub * batch_size, 2),
            "logistics_total_rub": round(self.logistics_cost_rub, 2),
            "overhead_rub": round(overhead, 2),
            "total_cost_rub": round(total_cost, 2),
            "unit_cost_rub": round(unit_cost, 2),
        }


class CostEngineer:
    """Core AI Cost Engineering service for rapid quoting and alternative route modeling."""

    @staticmethod
    def generate_three_routes(
        part_name: str,
        material: str,
        weight_kg: float,
        base_metal_price_per_kg: float,
        is_hollow_or_flange: bool = False,
    ) -> List[ManufacturingRoute]:
        """Generates 3 technological routes:

        1. Baseline (консервативный цеховой маршрут, сплошной пруток в стружку, розничный металл)
        2. Optimized In-House (прогрессивный инструмент, корончатый рез/труба, оптовый пул -10%)
        3. Subcontract & Finish (кооперация по заготовке + чистовое ЧПУ в своем цеху)
        """
        # Маршрут 1: Традиционный цеховой
        route_1 = ManufacturingRoute(
            route_id="ROUTE-A-BASELINE",
            description="Традиционный токарно-винторезный / стандартный ЧПУ (розничная заготовка, полное высверливание в стружку)",
            raw_material_cost_rub=weight_kg * base_metal_price_per_kg,
            waste_coefficient=2.2 if is_hollow_or_flange else 1.4,
            operations=[
                MachiningOperation("Отрезка заготовки", "Пила ленточная", 15, 6, 1200, 45),
                MachiningOperation(
                    "Черновая и чистовая токарная (стандартные режимы)",
                    "Токарный ЧПУ 1",
                    60,
                    28 if is_hollow_or_flange else 18,
                    2500,
                    180,
                ),
            ],
            logistics_cost_rub=17000.0,  # Завышенная отдельная доставка
            overhead_percent=0.18,
        )

        # Маршрут 2: Оптимизированный собственный (High-Efficiency Tooling + Procurement Pool)
        pooled_metal_price = base_metal_price_per_kg * 0.90  # Скидка 10% из пула
        waste_coef_opt = 1.35 if is_hollow_or_flange else 1.18  # Экономия металла (кольцевой рез или труба)

        route_2 = ManufacturingRoute(
            route_id="ROUTE-B-OPTIMIZED-INHOUSE",
            description="Оптимизированный ЧПУ (прогрессивные пластины, кольцевой съем/трубная заготовка, металл из оптового пула -10%, сборная доставка)",
            raw_material_cost_rub=weight_kg * pooled_metal_price,
            waste_coefficient=waste_coef_opt,
            operations=[
                MachiningOperation("Точный рез в размер", "ЧПУ пила", 10, 3.5, 1400, 35),
                MachiningOperation(
                    "Скоростная токарная обработка (Sandvik/Iscar геометрия)",
                    "Токарный ЧПУ 1",
                    40,
                    14 if is_hollow_or_flange else 10,
                    2500,
                    130,
                ),
            ],
            logistics_cost_rub=8500.0,  # Оптимизированный попутный догруз через АТИ.СУ
            overhead_percent=0.14,
        )

        # Маршрут 3: Кооперация (покупка готовой черновой поковки/отливки у партнера + чистовой контур)
        route_3 = ManufacturingRoute(
            route_id="ROUTE-C-COOPERATION",
            description="Кооперация (готовая отливка/заготовка на субподряде + прецизионная финишная ЧПУ обработка в своем цеху)",
            raw_material_cost_rub=0.0,
            waste_coefficient=1.05,
            subcontract_cost_rub=weight_kg * base_metal_price_per_kg * 1.15,  # Покупка черновой детали у партнера
            operations=[
                MachiningOperation(
                    "Финишное прецизионное точение и сверление отверстий",
                    "Токарный ЧПУ 1",
                    30,
                    7.5,
                    2500,
                    90,
                )
            ],
            logistics_cost_rub=6000.0,
            overhead_percent=0.12,
        )

        return [route_1, route_2, route_3]

    @staticmethod
    def analyze_competitive_bid(
        batch_size: int,
        baseline_cost_rub: float,
        baseline_quote_rub: float,
        competitor_price_rub: float,
        optimized_cost_rub: float,
        target_margin_percent: float = 0.22,
    ) -> Dict[str, any]:
        """Analyzes a competitive tender scenario (e.g.

        RegionStroy case):
        - Why the baseline quote failed
        - How the optimized route beats the competitor while safeguarding profit.
        """
        recommended_winning_price = round(optimized_cost_rub * (1.0 + target_margin_percent), 2)
        beats_competitor = recommended_winning_price < competitor_price_rub

        price_delta_to_competitor = round(recommended_winning_price - competitor_price_rub, 2)
        savings_against_baseline_cost = round(baseline_cost_rub - optimized_cost_rub, 2)
        projected_margin_rub = round(recommended_winning_price - optimized_cost_rub, 2)
        effective_margin_pct = round((projected_margin_rub / recommended_winning_price) * 100, 1)

        return {
            "baseline_quote_rub": baseline_quote_rub,
            "baseline_cost_rub": baseline_cost_rub,
            "competitor_price_rub": competitor_price_rub,
            "optimized_cost_rub": optimized_cost_rub,
            "recommended_winning_price_rub": recommended_winning_price,
            "beats_competitor": beats_competitor,
            "price_delta_to_competitor_rub": price_delta_to_competitor,
            "savings_against_baseline_cost_rub": savings_against_baseline_cost,
            "projected_margin_rub": projected_margin_rub,
            "effective_margin_percent": effective_margin_pct,
            "verdict": (
                "ПОБЕДА В ТЕНДЕРЕ С ВЫСОКОЙ МАРЖОЙ: Новая цена ниже конкурента, маржинальность обеспечена за счет оптимизации сырья, инструмента и логистики."
                if beats_competitor
                else "ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ОПТИМИЗАЦИЯ"
            ),
        }
