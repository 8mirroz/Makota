"""Makota Industrial OS: Vault Pilot Runner CLI.

Читает Markdown-карточки заказов из Obsidian Vault (YAML frontmatter) через engine/vault_parser.py,
вычисляет статусы SLA через OrderSLATracker, консолидирует потребности в сырье
через ProcurementMatcher, строит детерминированное расписание станков ЧПУ через ProductionPlanner
и формирует сводный отчёт для собственника.

Запуск:
    python3 engine/vault_runner.py --vault . --report reports/pilot_report.md
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Обеспечиваем корректный импорт engine.* при запуске как python3 engine/vault_runner.py
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.order_sla_tracker import OrderPipelineStatus, OrderSLATracker
from engine.procurement_matcher import (
    ProcurementMatcher,
    ProcurementPoolLot,
    RawStockRequirement,
)
from engine.production_planner import ProductionJob, ProductionPlanner, ScheduledSlot
from engine.vault_parser import (
    ORDERS_REL_DIR,
    REQUIRED_ORDER_FIELDS,
    VaultOrder,
    _extract_profile_and_dimension,
    _parse_datetime,
    _strip_yaml_scalar,
    _to_float,
    _to_int,
    load_vault_orders,
    parse_frontmatter,
    resolve_stage_entered_at,
    validate_vault_order_frontmatter,
)


def build_pilot_report(
    vault_dir: Path,
    now: Optional[datetime] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Формирует Markdown-отчёт и сводную статистику по заказам Vault."""
    ref_now = now or datetime.now()
    orders = load_vault_orders(vault_dir, now=ref_now)

    sla_statuses: List[OrderPipelineStatus] = []
    stock_requirements: List[RawStockRequirement] = []
    production_jobs: List[ProductionJob] = []

    for order in orders:
        sla = OrderSLATracker.evaluate_order_status(
            order_id=order.order_id,
            client=order.client,
            current_stage=order.status,
            entered_stage_at=order.entered_stage_at,
            now=ref_now,
        )
        sla_statuses.append(sla)

        if order.status in ("05_ожидание_сырья", "05_закупка_сырья_ожидание"):
            profile, dim = _extract_profile_and_dimension(order.raw_stock)
            # Оценочная масса и стоимость сырья (до получения точных спецификаций из 1С)
            est_weight_kg = max(100.0, float(order.quantity) * 2.0)
            est_raw_cost = round(order.estimated_cost_rub * 0.45, 2)
            stock_requirements.append(
                RawStockRequirement(
                    order_id=order.order_id,
                    client=order.client,
                    steel_grade=order.material,
                    profile_type=profile,
                    dimension_mm=dim,
                    weight_kg=est_weight_kg,
                    target_delivery_date=order.target_date,
                    estimated_base_price_rub=est_raw_cost,
                )
            )

        if order.status not in OrderSLATracker.TERMINAL_STAGES and order.status != "08_отгружен":
            production_jobs.append(
                ProductionJob(
                    order_id=order.order_id,
                    part_name=order.part_name,
                    material=order.material,
                    quantity=order.quantity,
                    target_date=order.target_date,
                    preferred_machine=order.machine if order.machine != "—" else "CNC-LATHE-01",
                    priority=order.priority,
                )
            )

    lots: List[ProcurementPoolLot] = (
        ProcurementMatcher.consolidate_requirements(stock_requirements)
        if stock_requirements
        else []
    )

    scheduled_slots: List[ScheduledSlot] = ProductionPlanner.schedule_jobs(
        production_jobs, start_at=ref_now.replace(hour=8, minute=0, second=0, microsecond=0)
    )

    alerts = [s for s in sla_statuses if s.risk_level in ("CRITICAL", "WARNING")]
    total_revenue = sum(o.quoted_price_rub for o in orders)
    total_cost = sum(o.estimated_cost_rub for o in orders)
    total_margin = sum(o.margin_rub for o in orders)
    margin_pct = (total_margin / total_revenue * 100.0) if total_revenue > 0 else 0.0
    total_pool_savings = sum(lot.savings_rub for lot in lots)

    lines: List[str] = [
        "# Сводный отчёт пилота Makota (Vault Runner)",
        "",
        f"> **Дата формирования**: {ref_now.strftime('%Y-%m-%d %H:%M')} | **Активных заказов**: {len(orders)}",
        "",
        "---",
        "",
        "## Сводка портфеля",
        "",
    ]

    if orders:
        lines.extend(
            [
                "| Заказ | Клиент | Деталь | Статус | Выручка (₽) | Себестоимость (₽) | Маржа (₽) | Дедлайн |",
                "|---|---|---|---|---:|---:|---:|---|",
            ]
        )
        for o in orders:
            lines.append(
                f"| `{o.order_id}` | {o.client} | {o.part_name} | `{o.status}` | "
                f"{o.quoted_price_rub:,.0f} | {o.estimated_cost_rub:,.0f} | "
                f"{o.margin_rub:,.0f} | {o.target_date} |"
            )
    else:
        lines.append("_Активных карточек заказов (`type: order`) в хранилище не найдено._")

    lines.extend(["", "---", "", "## SLA-алерты", ""])
    if alerts:
        for a in alerts:
            badge = "🔴 CRITICAL" if a.risk_level == "CRITICAL" else "🟡 WARNING"
            lines.append(
                f"- **{badge} | `{a.order_id}` ({a.client})**: {a.alert_message}"
            )
    else:
        lines.append("✅ Нарушений SLA по активным заказам не обнаружено.")

    lines.extend(["", "---", "", "## Пулы закупок металла", ""])
    if lots:
        lines.extend(
            [
                "| Пул | Марка | Профиль / Размер | Заказы | Вес (кг) | Скидка (%) | Экономия (₽) | Статус |",
                "|---|---|---|---|---:|---:|---:|---|",
            ]
        )
        for lot in lots:
            lines.append(
                f"| `{lot.pool_id}` | {lot.steel_grade} | {lot.profile_type} {lot.dimension_mm} | "
                f"{', '.join(lot.orders)} | {lot.total_weight_kg:,.1f} | "
                f"{lot.discount_percent:.1f}% | {lot.savings_rub:,.0f} | {lot.status} |"
            )
    else:
        lines.append("_Заказов на этапе ожидания сырья (`05_ожидание_сырья`) для пулинга не найдено._")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Расписание загрузки ЧПУ (Dynamic Scheduling)",
            "",
            ProductionPlanner.format_gantt_markdown(scheduled_slots),
            "",
            "---",
            "",
            "## Итог",
            "",
            f"- **Всего активных заказов**: {len(orders)}",
            f"- **Совокупная выручка портфеля**: {total_revenue:,.0f} ₽",
            f"- **Плановая себестоимость**: {total_cost:,.0f} ₽",
            f"- **Плановая валовая маржа**: {total_margin:,.0f} ₽ ({margin_pct:.1f}%)",
            f"- **Количество SLA-алертов (WARNING/CRITICAL)**: {len(alerts)}",
            f"- **Потенциальная экономия по пулам металла**: {total_pool_savings:,.0f} ₽",
            f"- **Сформировано слотов расписания ЧПУ**: {len(scheduled_slots)}",
            "",
        ]
    )

    stats = {
        "orders_count": len(orders),
        "alerts_count": len(alerts),
        "pools_count": len(lots),
        "scheduled_slots_count": len(scheduled_slots),
        "total_revenue_rub": total_revenue,
        "total_margin_rub": total_margin,
    }
    return "\n".join(lines), stats


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Makota Vault Runner — аудит заказов Obsidian Vault и генерация пилотного отчёта."
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=Path("."),
        help="Путь к корню Obsidian Vault (по умолчанию текущая директория).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/pilot_report.md"),
        help="Путь для сохранения сгенерированного Markdown-отчёта.",
    )
    parser.add_argument(
        "--now",
        type=str,
        default=None,
        help="Опциональная опорная дата/время (YYYY-MM-DDTHH:MM:SS) для детерминированной генерации отчёта.",
    )
    args = parser.parse_args(argv)

    ref_now = _parse_datetime(args.now, datetime.now()) if args.now else None
    report_md, stats = build_pilot_report(args.vault.resolve(), now=ref_now)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_md, encoding="utf-8")

    print(
        f"[OK] Отчёт сохранён: {args.report} "
        f"(заказов: {stats['orders_count']}, алертов SLA: {stats['alerts_count']}, пулов: {stats['pools_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
