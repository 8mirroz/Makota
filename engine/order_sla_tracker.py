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
    """Detects when an order sits idle between departments.

    Accepts both Obsidian Vault Russian-language status keys and legacy
    English SLA keys. See docs/contracts/status_contract.md for the full
    mapping table.
    """

    # Маппинг русских Vault-статусов и lifecycle_status из JSON Schema на внутренние SLA-ключи.
    # Источник истины: docs/contracts/status_contract.md
    STAGE_ALIASES: Dict[str, str] = {
        # Русские ключи (Obsidian Vault frontmatter) -> SLA-ключ
        "01_заявка_получена":              "01_lead_quoting",
        "02_расчет_КП":                    "01_lead_quoting",
        "03_КП_отправлено":                "02_client_approval",
        "04_заказ_подтвержден":            "02_client_approval",
        "05_ожидание_сырья":               "03_metal_procurement",
        "06_в_производстве":               "05_shop_floor_cnc",
        "07_контроль_ОТК":                 "06_final_qc",
        "08_отгружен":                     "07_dispatch",
        "09_закрыт_прибыль_зафиксирована": "07_dispatch",
        # lifecycle_status (digital_thread_order.schema.json) -> SLA-ключ
        "02_расчет_себестоимости":         "01_lead_quoting",
        "05_закупка_сырья_ожидание":       "03_metal_procurement",
        "06_сырье_на_складе":              "04_warehouse_inbound",
        "07_в_очереди_цеха":               "04_warehouse_inbound",
        "08_в_обработке_чпу":              "05_shop_floor_cnc",
        "09_контроль_качества_отк":        "06_final_qc",
        "10_отгружен_клиенту":             "07_dispatch",
        "11_закрыт_прибыль_зафиксирована": "07_dispatch",
        # Английские ключи (backward compatibility — не удалять)
        "01_lead_quoting":                 "01_lead_quoting",
        "02_client_approval":              "02_client_approval",
        "03_metal_procurement":            "03_metal_procurement",
        "04_warehouse_inbound":            "04_warehouse_inbound",
        "05_shop_floor_cnc":               "05_shop_floor_cnc",
        "06_final_qc":                     "06_final_qc",
        "07_dispatch":                     "07_dispatch",
    }

    DEFAULT_SLAS = {
        "01_lead_quoting":      (4.0,  "Отдел продаж & Cost Engineer"),
        "02_client_approval":   (48.0, "Отдел продаж"),
        "03_metal_procurement": (24.0, "Снабжение"),
        "04_warehouse_inbound": (12.0, "Склад & Входной контроль ОТК"),
        "05_shop_floor_cnc":    (72.0, "Цех механической обработки"),
        "06_final_qc":          (8.0,  "Служба ОТК"),
        "07_dispatch":          (6.0,  "Логистика и отгрузка"),
    }

    TERMINAL_STAGES = {
        "09_закрыт_прибыль_зафиксирована",
        "11_закрыт_прибыль_зафиксирована",
        "99_отменен",
        "99_отменен_проигран",
    }

    @classmethod
    def resolve_stage(cls, stage_key: str) -> str:
        """Нормализует ключ этапа: принимает как русские Vault-ключи, так и English SLA-ключи.

        Returns the canonical English SLA key used in DEFAULT_SLAS.
        Backward compatible: если передан уже английский ключ — возвращает как есть.
        """
        return cls.STAGE_ALIASES.get(stage_key, stage_key)

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

        hours_elapsed = max(0.0, (now - entered_stage_at).total_seconds() / 3600.0)

        # Завершённые или отменённые заказы не генерируют SLA-алертов
        if current_stage in cls.TERMINAL_STAGES:
            return OrderPipelineStatus(
                order_id=order_id,
                client=client,
                current_stage=current_stage,
                current_dept="Бухгалтерия / Архив",
                hours_in_stage=round(hours_elapsed, 1),
                max_sla_hours=0.0,
                is_breached=False,
                risk_level="OK",
                alert_message=None,
            )

        # Backward-compatible: поддерживаем как русские Vault-ключи, так и старые English-ключи
        resolved_stage = cls.resolve_stage(current_stage)
        sla_info = cls.DEFAULT_SLAS.get(resolved_stage, (24.0, "Общий контур"))
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
            current_stage=current_stage,  # сохраняем оригинальный ключ для трассируемости
            current_dept=dept,
            hours_in_stage=round(hours_elapsed, 1),
            max_sla_hours=max_sla_hours,
            is_breached=is_breached,
            risk_level=risk,
            alert_message=alert,
        )
