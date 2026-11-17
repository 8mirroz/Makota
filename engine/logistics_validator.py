"""Makota Industrial OS: Logistics & Freight Rate Benchmark Validator.

Prevents logistics cost leakage by validating freight rates against market corridors (ATI.SU benchmark),
detecting inflated quotes (e.g. 17,000 RUB vs 8,500 RUB), and recommending consolidated/shared cargo.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FreightBenchmark:
    route_name: str
    origin: str
    destination: str
    distance_km: float
    market_rate_dedicated_rub: float  # Отдельная машина (Газель/Валдай)
    market_rate_shared_rub: float     # Догруз / попутная машина (LTL)


class LogisticsValidator:
    """Validates requested transport costs against benchmark data corridor."""

    # Типовые логистические коридоры для металлопроката и заготовок (Урал - Поволжье)
    BENCHMARKS: Dict[str, FreightBenchmark] = {
        "CHELYABINSK_ALMETYEVSK": FreightBenchmark(
            route_name="Челябинск — Альметьевск",
            origin="Челябинск",
            destination="Альметьевск",
            distance_km=670,
            market_rate_dedicated_rub=19500.0,
            market_rate_shared_rub=8500.0,
        ),
        "KAZAN_ALMETYEVSK": FreightBenchmark(
            route_name="Казань — Альметьевск",
            origin="Казань",
            destination="Альметьевск",
            distance_km=260,
            market_rate_dedicated_rub=9500.0,
            market_rate_shared_rub=4200.0,
        ),
        "CHELNY_ALMETYEVSK": FreightBenchmark(
            route_name="Набережные Челны — Альметьевск",
            origin="Набережные Челны",
            destination="Альметьевск",
            distance_km=110,
            market_rate_dedicated_rub=5000.0,
            market_rate_shared_rub=2200.0,
        ),
    }

    @classmethod
    def evaluate_rate(
        cls,
        route_key: str,
        requested_rate_rub: float,
        cargo_weight_kg: float,
        is_urgent: bool = False,
    ) -> Dict[str, any]:
        """Evaluates whether the requested transport rate is fair or inflated."""
        benchmark = cls.BENCHMARKS.get(route_key.upper())

        if not benchmark:
            # Дефолтный эвристический расчет (25 руб./км для догруза, 45 руб./км для отдельной)
            return {
                "route": route_key,
                "status": "UNVERIFIED_CORRIDOR",
                "message": "Маршрут отсутствует в справочнике, требуется ручная проверка АТИ.СУ",
                "savings_potential_rub": 0.0,
            }

        # Если вес меньше 1500 кг и нет критичной спешки — оптимален догруз
        target_rate = benchmark.market_rate_dedicated_rub if is_urgent or cargo_weight_kg > 2500 else benchmark.market_rate_shared_rub
        delta = requested_rate_rub - target_rate

        is_inflated = delta > 2000.0
        overpay_percent = (delta / target_rate) * 100 if delta > 0 else 0.0

        recommendation = (
            f"ВНИМАНИЕ: Ставка логиста ({requested_rate_rub:,.0f} ₽) завышена на {overpay_percent:.1f}%. "
            f"Рыночная ставка попутного догруза на АТИ.СУ: {target_rate:,.0f} ₽. "
            f"Рекомендуется оформить сборный груз, чистая экономия: {delta:,.0f} ₽."
            if is_inflated
            else "Ставка соответствует рыночному коридору АТИ.СУ."
        )

        return {
            "route_name": benchmark.route_name,
            "cargo_weight_kg": cargo_weight_kg,
            "requested_rate_rub": requested_rate_rub,
            "benchmark_market_rate_rub": target_rate,
            "is_inflated": is_inflated,
            "overpay_percent": round(overpay_percent, 1),
            "savings_potential_rub": max(0.0, round(delta, 2)),
            "recommendation": recommendation,
        }
