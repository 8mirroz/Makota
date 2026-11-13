# Makota — Пульт управления Industrial Intelligence 2026

> **Текущий статус**: Реализация Фазы 1 (Инженерный фундамент и спецификации)  
> **Версия архитектуры**: Industrial Intelligence Core v2.0  
> **Последнее обновление**: 2026-11-14

---

## 🏭 Индустриальная операционная система: Архитектурные слои

| Слой | Назначение | Статус спецификации | Спецификация / Артефакт |
|---|---|---|---|
| **01. Digital Thread** | Сквозной цифровой паспорт заказа (ISO 23247) | ✅ Готово | [`specs/schemas/digital_thread_order.schema.json`](specs/schemas/digital_thread_order.schema.json) |
| **02. AI Cost Engineering** | Моделирование альтернатив и расчет себестоимости | ✅ Готово | [`specs/agents/cost_engineer_spec.md`](specs/agents/cost_engineer_spec.md) |
| **03. Dynamic Scheduling** | Алгоритмическое расписание ЧПУ (без LLM) | 🟡 В разработке | `specs/agents/production_planner_spec.md` |
| **04. Constraint Intel** | Мониторинг узких мест и «бегунок» (Order Controller) | ✅ Готово | [`specs/agents/order_controller_spec.md`](specs/agents/order_controller_spec.md) |
| **05. Quality Intelligence** | Замкнутый контур точности и CMM-замеры | 🟡 В разработке | `specs/schemas/qc_protocol.schema.json` |
| **06. Knowledge Graph** | Технологическая память и онтология металлообработки | ✅ Готово | [`specs/ontology/manufacturing_knowledge_graph.ttl`](specs/ontology/manufacturing_knowledge_graph.ttl) |
| **07. Make-or-Buy** | Точка безразличия: свое ЧПУ vs Субподряд | ⏳ Ожидает | Включено в Cost Engineer |
| **08. Procurement Pool** | Агрегация заказов металла в оптовые лоты | ✅ Готово | [`specs/agents/procurement_pool_spec.md`](specs/agents/procurement_pool_spec.md) |
| **09. CNC Telemetry** | Edge-мониторинг станков ЧПУ (OPC UA / MTConnect) | ✅ Готово | [`specs/schemas/machine_telemetry.schema.json`](specs/schemas/machine_telemetry.schema.json) |
| **10. Tool Registry** | Учет стойкости режущего инструмента и пластин | ✅ Готово | [`specs/schemas/tool_registry.schema.json`](specs/schemas/tool_registry.schema.json) |

---

## 📊 Финансовые метрики проекта (CFO: Модель внедрения Industrial OS)

| Метрика | Значение | Оценка |
|---|---|---|
| **Стоимость пилота завода** | 150 000 руб./мес | Рыночный оптимум для B2B |
| **Маржинальность контракта** | **67%** (100 000 руб./мес с клиента) | Высокая доходность консалтинга + софта |
| **Точка безубыточности (Break-even)** | **2.5 контракта/мес** | Полная защита постоянных затрат (250 тыс. руб.) |
| **План первого года (5 заводов)** | **2.97 млн руб. чистой прибыли** | При выручке 8.96 млн руб. |
| **Срок окупаемости стартовых инвестиций** | **2-й месяц** | Быстрый возврат затрат ($300 тыс. руб.) |
| **Стресс-тест (-10% к цене)** | 26% маржи (+$2.07 млн прибыли) | Запас прочности модели подтвержден |

Полный финансовый расчет: [`founder/cfo.md`](founder/cfo.md)

---

## 🎯 90-Дневная Дорожная Карта Пилота

```
[Фаза 1: Дни 1-15] Диагностика 30-50 заказов + Карта потерь ──────────────► В ТЕКУЩЕЙ РАБОТЕ
[Фаза 2: Дни 16-30] Слой данных: Digital Thread + 1C + 2 ЧПУ (Read-Only)
[Фаза 3: Дни 31-60] Три пилота: Cost Engineer + Order Controller + Tooling
[Фаза 4: Дни 61-90] Аудит экономики в рублях + Защита тиражирования
```

---

## 🛠 Быстрые команды валидации

```bash
# Валидация JSON схем
python3 -c "import json, jsonschema; [jsonschema.Draft202012Validator.check_schema(json.load(open(f))) for f in ['specs/schemas/digital_thread_order.schema.json', 'specs/schemas/machine_telemetry.schema.json', 'specs/schemas/tool_registry.schema.json']]; print('✅ Все схемы валидны')"

# Прогон тестового люкса
python3 -m unittest discover -s tests -v

# Юнит-экономика
python3 skills/founder-cfo/unit_economics.py founder/numbers.json
```
