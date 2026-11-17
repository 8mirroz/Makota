"""Makota Industrial OS: Order Controller & Digital Runner (Бегунок) SLA Tracker.

Monitors the lifecycle of orders across departmental handoffs (Sales -> Procurement -> Warehouse -> CNC -> QC),
detects unaddressed bottlenecks, and enforces SLA timers to eliminate multi-day dead times.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class OrderMilestone:
    stage_id: str
    stage_name: str
    entered_at: datetime
    max_sla_hours: float
    responsible_dept: str
    completed_at: Optional[datetime] = None


@dataclass
class OrderPipelineStatus:
    order_id: str
    client: str
    current_stage: str
    current_dept: str
    hours_in_stage: float
    max_sla_hours: float
    is_breached: bool
    risk_level: str  # "OK", "WARNING", "CRITICAL"
    alert_message: Optional[str] = None


class OrderSLATracker:
    """Detects when an order sits idle between departments."""

    DEFAULT_SLAS = {
        "01_lead_quoting": (4.0, "Отдел продаж & Cost Engineer"),
        "02_client_approval": (48.0, "Отдел продаж"),
        "03_metal_procurement": (24.0, "Снабжение"),
        "04_warehouse_inbound": (12.0, "Склад & Входной контроль ОТК"),
        "05_shop_floor_cnc": (72.0, "Цех механической обработки"),
        "06_final_qc": (8.0, "Служба ОТК"),
        "07_dispatch": (6.0, "Логистика и отгрузка"),
    }

    @classmethod
    def evaluate_order_status(
        cls,
        order_id: str,
        client: str,
        current_stage: str,
        entered_stage_at: datetime,
        now: Optional[datetime] = None,
    ) -> OrderPipelineStatus:
        if now is None:
            now = datetime.now()

        hours_elapsed = (now - entered_stage_at).total_seconds() / 3600.0
        sla_info = cls.DEFAULT_SLAS.get(current_stage, (24.0, "Общий контур"))
        max_sla_hours, dept = sla_info

        is_breached = hours_elapsed > max_sla_hours
        ratio = hours_elapsed / max_sla_hours

        if ratio >= 1.5:
            risk = "CRITICAL"
            alert = f"КРИТИЧЕСКИЙ СРЫВ SLA в отделе [{dept}]: Заказ находится на этапе {hours_elapsed:.1f} ч при нормативе {max_sla_hours:.1f} ч! Требуется эскалация директору."
        elif ratio >= 1.0:
            risk = "WARNING"
            alert = f"ПРЕДУПРЕЖДЕНИЕ: Превышен норматив передачи в отделе [{dept}] ({hours_elapsed:.1f} ч / {max_sla_hours:.1f} ч)."
        else:
            risk = "OK"
            alert = None

        return OrderPipelineStatus(
            order_id=order_id,
            client=client,
            current_stage=current_stage,
            current_dept=dept,
            hours_in_stage=round(hours_elapsed, 1),
            max_sla_hours=max_sla_hours,
            is_breached=is_breached,
            risk_level=risk,
            alert_message=alert,
        )
