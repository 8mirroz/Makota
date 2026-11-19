"""Makota Industrial OS: Dynamic Production Scheduler (Алгоритмическое расписание ЧПУ).

Implements deterministic Earliest Due Date (EDD) and sequence-dependent setup time
scheduling without LLM involvement, compliant with specs/agents/production_planner_spec.md
and ISA/IEC 62443 (read-only planning, human-in-the-loop dispatch approval).
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ProductionJob:
    order_id: str
    part_name: str
    material: str
    quantity: int
    target_date: str  # YYYY-MM-DD
    preferred_machine: str = "CNC-LATHE-01"
    unit_machining_time_min: float = 12.0
    priority: str = "Нормальный"


@dataclass
class ScheduledSlot:
    machine_id: str
    order_id: str
    part_name: str
    material: str
    quantity: int
    start_time: datetime
    end_time: datetime
    setup_time_min: float
    machining_hours: float
    target_date: str
    is_tardy: bool
    risk_badge: str


class ProductionPlanner:
    """Deterministic EDD + sequence-dependent setup scheduler for CNC machines."""

    DEFAULT_SETUP_TIMES_MIN: Dict[str, float] = {
        "steel_to_bronze": 30.0,
        "steel_to_stainless": 45.0,
        "bronze_to_steel": 30.0,
        "bronze_to_stainless": 40.0,
        "stainless_to_steel": 45.0,
        "stainless_to_bronze": 40.0,
        "same_material": 10.0,
        "diameter_change_large": 20.0,
    }

    DEFAULT_MATERIAL_GROUPS: Dict[str, str] = {
        "40Х": "steel",
        "09Г2С": "steel",
        "45": "steel",
        "12Х18Н10Т": "stainless",
        "БрАЖ9-4": "bronze",
        "Д16Т": "aluminum",
    }

    @classmethod
    def load_setup_matrix(cls, matrix_path: Optional[Path] = None) -> Dict[str, float]:
        if matrix_path is None:
            matrix_path = (
                Path(__file__).resolve().parent.parent
                / "specs"
                / "agents"
                / "planner_setup_matrix.json"
            )
        if matrix_path.exists():
            try:
                data = json.loads(matrix_path.read_text(encoding="utf-8"))
                return {
                    k: float(v)
                    for k, v in data.get("setup_times_min", cls.DEFAULT_SETUP_TIMES_MIN).items()
                }
            except (OSError, ValueError, TypeError):
                pass
        return dict(cls.DEFAULT_SETUP_TIMES_MIN)

    @classmethod
    def classify_material_group(cls, material: str) -> str:
        norm = material.strip().upper()
        for key, group in cls.DEFAULT_MATERIAL_GROUPS.items():
            if key.upper() in norm:
                return group
        if "БР" in norm:
            return "bronze"
        if "12Х18" in norm or "НЕРЖ" in norm:
            return "stainless"
        return "steel"

    @classmethod
    def compute_setup_time_min(
        cls,
        prev_material: Optional[str],
        next_material: str,
        setup_matrix: Optional[Dict[str, float]] = None,
    ) -> float:
        """Calculates changeover setup time in minutes between consecutive jobs on a machine."""
        if prev_material is None:
            return 0.0
        matrix = setup_matrix or cls.DEFAULT_SETUP_TIMES_MIN
        if prev_material.strip().upper() == next_material.strip().upper():
            return matrix.get("same_material", 10.0)
        g_prev = cls.classify_material_group(prev_material)
        g_next = cls.classify_material_group(next_material)
        if g_prev == g_next:
            return matrix.get("same_material", 10.0)
        transition_key = f"{g_prev}_to_{g_next}"
        return matrix.get(transition_key, 30.0)

    @staticmethod
    def _parse_due_date(target_date: str, fallback: datetime) -> datetime:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(target_date.strip(), fmt)
                return dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                continue
        return fallback + timedelta(days=14)

    @classmethod
    def schedule_jobs(
        cls,
        jobs: List[ProductionJob],
        start_at: Optional[datetime] = None,
        available_machines: Optional[List[str]] = None,
        matrix_path: Optional[Path] = None,
    ) -> List[ScheduledSlot]:
        """Schedules jobs using Earliest Due Date (EDD) with material changeover setup penalties."""
        if not jobs:
            return []

        ref_start = start_at or datetime(2026, 11, 18, 8, 0, 0)
        machines = available_machines or ["CNC-LATHE-01", "VMC-5AXIS-02"]
        setup_matrix = cls.load_setup_matrix(matrix_path)

        # Sort by Earliest Due Date (EDD), then priority ("Срочный" first), then order_id
        def _sort_key(job: ProductionJob):
            due = cls._parse_due_date(job.target_date, ref_start)
            prio_rank = 0 if job.priority.strip().lower() == "срочный" else 1
            return (due, prio_rank, job.order_id)

        sorted_jobs = sorted(jobs, key=_sort_key)

        machine_clock: Dict[str, datetime] = {m: ref_start for m in machines}
        machine_last_material: Dict[str, Optional[str]] = {m: None for m in machines}
        schedule: List[ScheduledSlot] = []

        for job in sorted_jobs:
            target_machine = (
                job.preferred_machine
                if job.preferred_machine in machine_clock
                else min(machine_clock, key=lambda m: machine_clock[m])
            )
            prev_mat = machine_last_material.get(target_machine)
            setup_min = cls.compute_setup_time_min(prev_mat, job.material, setup_matrix)

            slot_start = machine_clock[target_machine] + timedelta(minutes=setup_min)
            machining_min = max(1.0, float(job.quantity) * float(job.unit_machining_time_min))
            slot_end = slot_start + timedelta(minutes=machining_min)

            due_dt = cls._parse_due_date(job.target_date, ref_start)
            is_tardy = slot_end > due_dt
            risk_badge = "🔴 Риск срыва срока" if is_tardy else "✅ В срок"

            schedule.append(
                ScheduledSlot(
                    machine_id=target_machine,
                    order_id=job.order_id,
                    part_name=job.part_name,
                    material=job.material,
                    quantity=job.quantity,
                    start_time=slot_start,
                    end_time=slot_end,
                    setup_time_min=round(setup_min, 1),
                    machining_hours=round(machining_min / 60.0, 1),
                    target_date=job.target_date,
                    is_tardy=is_tardy,
                    risk_badge=risk_badge,
                )
            )

            machine_clock[target_machine] = slot_end
            machine_last_material[target_machine] = job.material

        return schedule

    @classmethod
    def format_gantt_markdown(cls, slots: List[ScheduledSlot]) -> str:
        """Formats scheduled slots into a Markdown Gantt table per production_planner_spec.md."""
        if not slots:
            return "_В очереди планирования ЧПУ нет активных производственных заданий._"

        lines = [
            "| Станок | Заказ | Деталь | Материал | Партия | Начало | Конец | Переналадка | Риск |",
            "|---|---|---|---|---:|---|---|---:|---|",
        ]
        for s in slots:
            setup_str = f"{s.setup_time_min:.0f} мин" if s.setup_time_min > 0 else "—"
            lines.append(
                f"| `{s.machine_id}` | `{s.order_id}` | {s.part_name} | {s.material} | "
                f"{s.quantity} шт | {s.start_time.strftime('%d.%m %H:%M')} | "
                f"{s.end_time.strftime('%d.%m %H:%M')} | {setup_str} | {s.risk_badge} |"
            )
        return "\n".join(lines)
