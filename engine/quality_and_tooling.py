"""Makota Industrial OS: Quality Intelligence (OTK / Cpk) & Tool Registry Wear Monitor.

Implements Layer 05 (Quality Intelligence, specs/schemas/qc_protocol.schema.json)
and Layer 10 (Tool Registry, specs/schemas/tool_registry.schema.json) with zero external
dependencies.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolLifeRecord:
    tool_id: str
    turret_position: str
    tool_type: str
    insert_type: str
    standard_life_min: float
    accumulated_cut_min: float
    insert_edge_cost_rub: float = 450.0


@dataclass
class ToolWearStatus:
    tool_id: str
    turret_position: str
    insert_type: str
    remaining_life_min: float
    wear_percent: float
    risk_level: str  # "OK", "WARNING", "CRITICAL"
    recommended_action: str


@dataclass
class DimensionMeasurement:
    feature: str
    nominal_mm: float
    upper_deviation_mm: float
    lower_deviation_mm: float
    measured_values_mm: List[float]


class QualityAndToolingEngine:
    """Deterministic tool wear tracker and statistical quality control (Cpk) evaluator."""

    @staticmethod
    def evaluate_tool_wear(record: ToolLifeRecord) -> ToolWearStatus:
        if record.standard_life_min <= 0:
            raise ValueError("Нормативная стойкость инструмента должна быть больше 0")

        rem = max(0.0, record.standard_life_min - record.accumulated_cut_min)
        wear_pct = (record.accumulated_cut_min / record.standard_life_min) * 100.0

        if wear_pct >= 95.0:
            risk = "CRITICAL"
            action = (
                f"КРИТИЧЕСКИЙ ИЗНОС [{record.turret_position} {record.insert_type}]: "
                f"остаток {rem:.1f} мин ({wear_pct:.0f}% ресурса). Немедленно повернуть/заменить кромку перед следующей деталью!"
            )
        elif wear_pct >= 80.0:
            risk = "WARNING"
            action = (
                f"ПЛАНОВАЯ ЗАМЕНА [{record.turret_position} {record.insert_type}]: "
                f"остаток {rem:.1f} мин ({wear_pct:.0f}% ресурса). Подготовить сменную кромку."
            )
        else:
            risk = "OK"
            action = "Ресурс в норме, работа в штатном режиме."

        return ToolWearStatus(
            tool_id=record.tool_id,
            turret_position=record.turret_position,
            insert_type=record.insert_type,
            remaining_life_min=round(rem, 1),
            wear_percent=round(wear_pct, 1),
            risk_level=risk,
            recommended_action=action,
        )

    @classmethod
    def audit_turret_magazine(cls, tools: List[ToolLifeRecord]) -> List[ToolWearStatus]:
        return [cls.evaluate_tool_wear(t) for t in tools]

    @staticmethod
    def evaluate_qc_measurements(
        protocol_id: str,
        order_id: str,
        batch_size: int,
        unit_cost_rub: float,
        measurement: DimensionMeasurement,
    ) -> Dict[str, Any]:
        """Evaluates dimensional measurements against tolerance limits and computes Cpk."""
        if not measurement.measured_values_mm:
            raise ValueError("Список замеров ОТК не может быть пустым")

        usl = measurement.nominal_mm + measurement.upper_deviation_mm
        lsl = measurement.nominal_mm + measurement.lower_deviation_mm
        vals = measurement.measured_values_mm
        n = len(vals)

        out_of_tol = [v for v in vals if v < lsl - 1e-9 or v > usl + 1e-9]
        scrap_count = len(out_of_tol)
        scrap_cost = round(scrap_count * unit_cost_rub, 2)

        mean_val = sum(vals) / n
        if n > 1:
            variance = sum((v - mean_val) ** 2 for v in vals) / (n - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        if std_dev > 1e-9:
            cpu = (usl - mean_val) / (3.0 * std_dev)
            cpl = (mean_val - lsl) / (3.0 * std_dev)
            cpk: Optional[float] = round(min(cpu, cpl), 2)
        else:
            cpk = 2.0 if scrap_count == 0 else 0.0

        if scrap_count == 0 and (cpk is None or cpk >= 1.33):
            verdict = "годен"
            recommendation = "Партия соответствует чертежу, процесс статистически стабилен (Cpk >= 1.33)."
        elif scrap_count == 0:
            verdict = "годен"
            recommendation = f"Размеры в допуске, но Cpk={cpk:.2f} < 1.33 (смещение к границе поля допуска). Ввести корректор износа на стойке ЧПУ."
        else:
            verdict = "брак" if scrap_count == n else "условно годен"
            recommendation = (
                f"Выявлено {scrap_count} дет. вне поля допуска [{lsl:.3f}..{usl:.3f} мм]. "
                f"Прямой ущерб: {scrap_cost:,.0f} ₽. Проверить износ чистовой пластины."
            )

        return {
            "protocol_id": protocol_id,
            "order_id": order_id,
            "feature": measurement.feature,
            "batch_size": batch_size,
            "inspected_count": n,
            "lsl_mm": round(lsl, 4),
            "usl_mm": round(usl, 4),
            "mean_mm": round(mean_val, 4),
            "cpk_index": cpk,
            "scrap_count": scrap_count,
            "scrap_cost_rub": scrap_cost,
            "overall_verdict": verdict,
            "recommendation": recommendation,
        }
