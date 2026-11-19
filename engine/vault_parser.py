"""Makota Industrial OS: Obsidian Vault Markdown & YAML Frontmatter Parser.

Provides zero-dependency parsing, timestamp priority resolution (stage_entered_at -> updated_at -> created_at),
and contract validation for Obsidian Vault order cards.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from engine.order_sla_tracker import OrderSLATracker

ORDERS_REL_DIR = Path("02_Продажи_и_Заказы") / "Активные_заказы"

REQUIRED_ORDER_FIELDS = (
    "order_id",
    "client",
    "part_name",
    "material",
    "quantity",
    "status",
    "target_date",
)


@dataclass
class VaultOrder:
    file_path: Path
    order_id: str
    client: str
    part_name: str
    material: str
    raw_stock: str
    quantity: int
    status: str
    target_date: str
    quoted_price_rub: float
    estimated_cost_rub: float
    margin_rub: float
    machine: str
    priority: str
    entered_stage_at: datetime


def _strip_yaml_scalar(raw: str) -> str:
    val = raw.strip()
    # Удаляем инлайновые комментарии вида: "01_заявка_получена" # [...]
    if val.startswith('"'):
        m = re.match(r'^"([^"]*)"', val)
        if m:
            return m.group(1)
    elif val.startswith("'"):
        m = re.match(r"^'([^']*)'", val)
        if m:
            return m.group(1)
    else:
        val = val.split("#", 1)[0].strip()
    return val


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Парсит плоский YAML frontmatter (без внешних зависимостей)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    data: Dict[str, Any] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_val = line.split(":", 1)
        data[key.strip()] = _strip_yaml_scalar(raw_val)
    return data


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(" ", "")))
    except (TypeError, ValueError):
        return default


def _parse_datetime(raw: Any, fallback: datetime) -> datetime:
    if not raw:
        return fallback
    text = str(raw).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return fallback


def resolve_stage_entered_at(fm: Dict[str, Any], fallback: datetime) -> datetime:
    """Определяет время входа заказа на текущий этап по приоритету:
    stage_entered_at -> updated_at -> created_at -> fallback.
    """
    raw_ts = (
        fm.get("stage_entered_at")
        or fm.get("updated_at")
        or fm.get("created_at")
    )
    return _parse_datetime(raw_ts, fallback)


def _extract_profile_and_dimension(raw_stock: str) -> Tuple[str, str]:
    lower = raw_stock.lower()
    profile = "круг"
    for candidate in ("труба", "шестигранник", "лист", "поковка", "круг"):
        if candidate in lower:
            profile = candidate
            break
    dim_match = re.search(r"(\d+(?:[xх×]\d+)?)", raw_stock)
    dimension = dim_match.group(1).replace("х", "x").replace("×", "x") if dim_match else "0"
    return profile, dimension


def validate_vault_order_frontmatter(fm: Dict[str, Any]) -> List[str]:
    """Проверяет карточку заказа на соответствие единому контракту статусов и обязательных полей."""
    errors: List[str] = []
    if fm.get("type") != "order":
        errors.append("Отсутствует или некорректен атрибут 'type: order'")
    for field in REQUIRED_ORDER_FIELDS:
        if not fm.get(field):
            errors.append(f"Отсутствует обязательное поле '{field}'")
    status = str(fm.get("status") or "")
    valid_statuses = set(OrderSLATracker.STAGE_ALIASES.keys()) | set(OrderSLATracker.TERMINAL_STAGES)
    if status and status not in valid_statuses:
        errors.append(f"Неизвестный статус заказа '{status}' (нарушение docs/contracts/status_contract.md)")
    return errors


def load_vault_orders(vault_dir: Path, now: Optional[datetime] = None) -> List[VaultOrder]:
    """Сканирует 02_Продажи_и_Заказы/Активные_заказы/*.md и возвращает карточки с type: order."""
    orders_dir = vault_dir / ORDERS_REL_DIR
    if not orders_dir.exists():
        return []

    ref_now = now or datetime.now()
    orders: List[VaultOrder] = []

    for md_path in sorted(orders_dir.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm.get("type") != "order":
            continue

        entered_at = resolve_stage_entered_at(fm, ref_now)
        quoted = _to_float(fm.get("quoted_price_rub"))
        est_cost = _to_float(fm.get("estimated_cost_rub"))
        margin = _to_float(fm.get("margin_rub"), quoted - est_cost)

        orders.append(
            VaultOrder(
                file_path=md_path,
                order_id=str(fm.get("order_id") or md_path.stem),
                client=str(fm.get("client") or "Не указан"),
                part_name=str(fm.get("part_name") or "Без названия"),
                material=str(fm.get("material") or "—"),
                raw_stock=str(fm.get("raw_stock") or ""),
                quantity=_to_int(fm.get("quantity"), 1),
                status=str(fm.get("status") or "01_заявка_получена"),
                target_date=str(fm.get("target_date") or "—"),
                quoted_price_rub=quoted,
                estimated_cost_rub=est_cost,
                margin_rub=margin,
                machine=str(fm.get("machine") or "—"),
                priority=str(fm.get("priority") or "Нормальный"),
                entered_stage_at=entered_at,
            )
        )

    return orders
