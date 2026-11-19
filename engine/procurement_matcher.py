"""Makota Industrial OS: Procurement Pool Matcher Engine.

Consolidates raw material requirements from multiple incoming orders into
wholesale bulk purchasing lots to capture 7-15% volume discounts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional


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

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def _split_by_date_window(
        cls,
        req_list: List[RawStockRequirement],
        max_date_delta_days: int,
    ) -> List[List[RawStockRequirement]]:
        """Splits a material group into temporal clusters within max_date_delta_days."""
        if max_date_delta_days <= 0 or len(req_list) <= 1:
            return [req_list]

        dated = [(r, cls._parse_date(r.target_delivery_date)) for r in req_list]
        with_dates = [(r, d) for r, d in dated if d is not None]
        without_dates = [r for r, d in dated if d is None]

        if not with_dates:
            return [req_list]

        with_dates.sort(key=lambda item: item[1])
        clusters: List[List[RawStockRequirement]] = []
        current_cluster: List[RawStockRequirement] = [with_dates[0][0]]
        anchor_date: datetime = with_dates[0][1]

        for req, req_date in with_dates[1:]:
            if (req_date - anchor_date) <= timedelta(days=max_date_delta_days):
                current_cluster.append(req)
            else:
                clusters.append(current_cluster)
                current_cluster = [req]
                anchor_date = req_date

        clusters.append(current_cluster)
        if without_dates:
            clusters[0].extend(without_dates)
        return clusters

    @classmethod
    def consolidate_requirements(
        cls,
        requirements: List[RawStockRequirement],
        max_date_delta_days: int = 10,
    ) -> List[ProcurementPoolLot]:
        """Groups requirements by steel grade, profile, compatible dimensions, and temporal window."""
        grouped: Dict[str, List[RawStockRequirement]] = {}

        for req in requirements:
            key = f"{req.steel_grade.strip().upper()}_{req.profile_type.strip().lower()}_{req.dimension_mm.strip()}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(req)

        lots: List[ProcurementPoolLot] = []

        for key, req_list in grouped.items():
            temporal_clusters = cls._split_by_date_window(req_list, max_date_delta_days)

            for idx, cluster in enumerate(temporal_clusters):
                steel_grade = cluster[0].steel_grade
                profile_type = cluster[0].profile_type
                dim = cluster[0].dimension_mm
                order_ids = [r.order_id for r in cluster]

                total_weight = sum(r.weight_kg for r in cluster)
                base_total_cost = sum(r.estimated_base_price_rub for r in cluster)

                discount_pct = cls.get_discount_for_weight(total_weight)
                discounted_cost = base_total_cost * (1.0 - discount_pct)
                savings = base_total_cost - discounted_cost

                base_pool_id = f"POOL-{steel_grade}-{dim.replace('x', '_')}"
                pool_id = base_pool_id if idx == 0 else f"{base_pool_id}-W{idx + 1}"
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
