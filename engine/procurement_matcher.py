"""Makota Industrial OS: Procurement Pool Matcher Engine.

Consolidates raw material requirements from multiple incoming orders into
wholesale bulk purchasing lots to capture 7-15% volume discounts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class RawStockRequirement:
    order_id: str
    client: str
    steel_grade: str
    profile_type: str  # e.g., "круг", "труба", "лист", "шестигранник"
    dimension_mm: str  # e.g., "150", "85x55", "70", "24"
    weight_kg: float
    target_delivery_date: str  # YYYY-MM-DD
    estimated_base_price_rub: float


@dataclass
class ProcurementPoolLot:
    pool_id: str
    steel_grade: str
    profile_type: str
    dimension_mm: str
    orders: List[str]
    total_weight_kg: float
    base_cost_rub: float
    discount_percent: float
    discounted_cost_rub: float
    savings_rub: float
    status: str


class ProcurementMatcher:
    """Consolidation algorithm that clusters requirements into actionable wholesale purchasing pools."""

    # Шкала оптовых скидок в зависимости от тоннажа лота
    DISCOUNT_TIERS = [
        (5000.0, 0.14),  # от 5 тонн: -14%
        (2000.0, 0.10),  # от 2 тонн: -10%
        (1000.0, 0.07),  # от 1 тонны: -7%
        (500.0, 0.04),   # от 500 кг: -4%
        (0.0, 0.00),     # розница: 0%
    ]

    @classmethod
    def get_discount_for_weight(cls, total_weight_kg: float) -> float:
        for threshold, discount in cls.DISCOUNT_TIERS:
            if total_weight_kg >= threshold:
                return discount
        return 0.0

    @classmethod
    def consolidate_requirements(
        cls,
        requirements: List[RawStockRequirement],
        max_date_delta_days: int = 10,
    ) -> List[ProcurementPoolLot]:
        """Groups requirements by steel grade, profile and compatible dimensions."""
        grouped: Dict[str, List[RawStockRequirement]] = {}

        for req in requirements:
            key = f"{req.steel_grade.strip().upper()}_{req.profile_type.strip().lower()}_{req.dimension_mm.strip()}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(req)

        lots: List[ProcurementPoolLot] = []

        for key, req_list in grouped.items():
            steel_grade = req_list[0].steel_grade
            profile_type = req_list[0].profile_type
            dim = req_list[0].dimension_mm
            order_ids = [r.order_id for r in req_list]

            total_weight = sum(r.weight_kg for r in req_list)
            base_total_cost = sum(r.estimated_base_price_rub for r in req_list)

            discount_pct = cls.get_discount_for_weight(total_weight)
            discounted_cost = base_total_cost * (1.0 - discount_pct)
            savings = base_total_cost - discounted_cost

            pool_id = f"POOL-{steel_grade}-{dim.replace('x', '_')}"
            status = "ГОТОВ К ЗАКУПКЕ" if total_weight >= 1000.0 else "СБОР ОБЪЕМА"

            lots.append(
                ProcurementPoolLot(
                    pool_id=pool_id,
                    steel_grade=steel_grade,
                    profile_type=profile_type,
                    dimension_mm=dim,
                    orders=order_ids,
                    total_weight_kg=round(total_weight, 2),
                    base_cost_rub=round(base_total_cost, 2),
                    discount_percent=round(discount_pct * 100, 1),
                    discounted_cost_rub=round(discounted_cost, 2),
                    savings_rub=round(savings, 2),
                    status=status,
                )
            )

        return sorted(lots, key=lambda l: l.savings_rub, reverse=True)
