# Makota — Пульт управления Industrial Intelligence 2026

> **Текущий статус**: Готовый демонстрационный стенд для собственника производства (Трек A — «Пилот у владельца»)  
> **Версия архитектуры**: Industrial Intelligence Core v2.1 (оценка архитектурного аудита: **A / 96 баллов**)  
> **Быстрый вход**: [Презентация проекта (`PRESENTATION.md`)](PRESENTATION.md) • [Инструкция и Онбординг (`ONBOARDING.md`)](ONBOARDING.md) • [Интерактивный HTML-дашборд (`reports/makota_interactive_dashboard.html`)](reports/makota_interactive_dashboard.html)

---

## 🎯 1. Навигация по материалам для собственника и дирекции завода

| Документ / Инструмент | Готовность | Ссылка и назначение |
|---|:---:|---|
| **Презентация проекта (простым деловым языком)** | ✅ Готов | [`PRESENTATION.md`](PRESENTATION.md) и [`01_Дирекция/Пилотный_демо_презент_Makota_AI.md`](01_Дирекция/Пилотный_демо_презент_Makota_AI.md) |
| **Инструкция по функциям, наполнению и настройке** | ✅ Готов | [`ONBOARDING.md`](ONBOARDING.md) и [`01_Дирекция/Инструкция_и_Онбординг_Makota.md`](01_Дирекция/Инструкция_и_Онбординг_Makota.md) |
| **Интерактивный симулятор и пульт в браузере (6 вкладок)** | ✅ Готов | [`reports/makota_interactive_dashboard.html`](reports/makota_interactive_dashboard.html) (открывается двойным кликом без интернета) |
| **Автоматический сводный отчёт по портфелю заказов** | ✅ Готов | [`reports/pilot_report.md`](reports/pilot_report.md) (генерируется ядром `engine/vault_runner.py`) |
| **Демонстрация всех 6 расчётных модулей в 1 клик** | ✅ Готов | [`engine/demo_showcase.py`](engine/demo_showcase.py) (`python3 engine/demo_showcase.py`) |
| **Чек-лист исходных данных для старта пилота на заводе** | ✅ Готов | [`reports/data_request.md`](reports/data_request.md) |
| **План проведения 1-дневного визита на производство** | ✅ Готов | [`docs/visit/visit-checklist.md`](docs/visit/visit-checklist.md) • [`docs/visit/service-blueprint.md`](docs/visit/service-blueprint.md) |
| **Мировые бенчмарки и справочный пакет 130 workflow** | 📚 Справочник | [`docs/BENCHMARKS_AND_CASE_STUDIES.md`](docs/BENCHMARKS_AND_CASE_STUDIES.md) • [`01_Дирекция/Пакет_собственника_2026-11-17/00_Оглавление.md`](01_Дирекция/Пакет_собственника_2026-11-17/00_Оглавление.md) |

---

## 🏭 2. Десять архитектурных слоёв системы (100% реализовано в коде и спецификациях)

| Слой | Назначение для завода | Статус | Реализация в коде и спецификациях |
|---|---|:---:|---|
| **01. Digital Thread** | Сквозной цифровой паспорт заказа от чертежа до P&L (ISO 23247) | ✅ Готово | [`specs/schemas/digital_thread_order.schema.json`](specs/schemas/digital_thread_order.schema.json) • [`engine/vault_parser.py`](engine/vault_parser.py) |
| **02. AI Cost Engineering** | Расчёт 3 альтернативных маршрутов изготовления и победной цены тендера | ✅ Готово | [`engine/cost_calculator.py`](engine/cost_calculator.py) • [`specs/agents/cost_engineer_spec.md`](specs/agents/cost_engineer_spec.md) |
| **03. Dynamic Scheduling** | Алгоритмическое расписание парка ЧПУ по правилу EDD с матрицей переналадок | ✅ Готово | [`engine/production_planner.py`](engine/production_planner.py) • [`specs/agents/production_planner_spec.md`](specs/agents/production_planner_spec.md) |
| **04. Constraint Intel** | «Цифровой бегунок» — контроль SLA отделов и блокировка простоев | ✅ Готово | [`engine/order_sla_tracker.py`](engine/order_sla_tracker.py) • [`specs/agents/order_controller_spec.md`](specs/agents/order_controller_spec.md) |
| **05. Quality Intelligence** | Контроль допусков ОТК, расчёт индекса точности $C_{pk}$ и стоимости брака | ✅ Готово | [`engine/quality_and_tooling.py`](engine/quality_and_tooling.py) • [`specs/schemas/qc_protocol.schema.json`](specs/schemas/qc_protocol.schema.json) |
| **06. Knowledge Graph** | Технологическая память завода: сплавы, режимы резания, устранение вибраций | ✅ Готово | [`specs/ontology/manufacturing_knowledge_graph.ttl`](specs/ontology/manufacturing_knowledge_graph.ttl) • `05_База_Знаний/` |
| **07. Make-or-Buy ($N^*$)** | Расчёт точки безразличия партии: точить в своём цеху или отдать на кооперацию | ✅ Готово | [`engine/cost_calculator.py`](engine/cost_calculator.py) (`evaluate_make_or_buy`) |
| **08. Procurement Pool** | Объединение заказов на металл в оптовые лоты со скидкой 7–14% | ✅ Готово | [`engine/procurement_matcher.py`](engine/procurement_matcher.py) • [`specs/agents/procurement_pool_spec.md`](specs/agents/procurement_pool_spec.md) |
| **09. CNC Telemetry & Logistics** | Read-Only мониторинг станков (ISA/IEC 62443) + проверка ставок АТИ.СУ | ✅ Готово | [`engine/logistics_validator.py`](engine/logistics_validator.py) • [`specs/schemas/machine_telemetry.schema.json`](specs/schemas/machine_telemetry.schema.json) |
| **10. Tool Registry** | Поминутный учёт ресурса твердосплавных пластин и предупреждение до брака | ✅ Готово | [`engine/quality_and_tooling.py`](engine/quality_and_tooling.py) • [`specs/schemas/tool_registry.schema.json`](specs/schemas/tool_registry.schema.json) |

---

## 💰 3. Целевая экономика внедрения для завода-заказчика

| Показатель эффективности на производстве | До внедрения Makota | С системой Makota Industrial OS | Источник эффекта |
|---|---|---|---|
| **Время расчёта КП по чертежам** | 1–3 рабочих дня | **15–30 минут** (3 маршрута сразу) | Автоматический расчёт в `CostEngineer` |
| **Затраты на металлопрокат** | Розничная закупка под 1 заказ | **Скидка 7–14%** на тоннаже | Оптовая консолидация в `ProcurementMatcher` |
| **Затраты на доставку металла** | Отдельная машина (переплата до 100%) | **Рыночный тариф догруза АТИ.СУ** | Авто-проверка в `LogisticsValidator` |
| **Потери времени на стыках отделов** | До 5–14 дней «забытых» заявок | **Алерт в день превышения SLA** | Контроль этапов в `OrderSLATracker` |
| **Пример: Тендер «РегионСтрой» (150 фланцев 40Х)** | С/с 100 000 ₽ → КП 137 000 ₽ (**Проигрыш**) | С/с **76 800 ₽** → КП **98 400 ₽** (**Победа, +21 600 ₽ прибыли**) | Пул металла (-8.2к) + режимы (-6.5к) + догруз (-8.5к) |

---

## 🗓️ 4. Дорожная карта настройки и интеграции под ваше предприятие (90 дней)

```
[Шаг 0: 48 часов]    Тестовый прогон ваших 5-10 заказов и тендеров ────► Расчёт точной экономии в рублях
[Фаза 1: Дни 1-30]   Настройка марок сталей, поставщиков и SLA ────────► Запуск оптовых пулов и «Цифрового бегунка»
[Фаза 2: Дни 31-60]  Калибровка ставок станко-часа и связка с 1С ──────► Расчёт 3 маршрутов КП за 15 минут + очередь ЧПУ
[Фаза 3: Дни 61-90]  Штрихкоды в цеху + контроль пластин + обучение ───► Сдача системы под ключ и аудит экономии
```

---

## 🛠 5. Быстрые команды проверки и демонстрации

```bash
# 1. Наглядная демонстрация работы всех 6 модулей ядра на экране:
python3 engine/demo_showcase.py

# 2. Сборка актуального сводного отчёта по карточкам заказов Obsidian Vault:
python3 engine/vault_runner.py --vault . --report reports/pilot_report.md

# 3. Запуск полного набора автотестов (алгоритмы, JSON-схемы, карточки заказов):
python3 -m unittest discover -s tests -v
```
