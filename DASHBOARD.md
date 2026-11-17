# Makota — Пульт управления Industrial Intelligence 2026

> **Текущий статус**: Трек A — «Пилот у владельца» (канонический, решение 2026-11-14)
> **Версия архитектуры**: Industrial Intelligence Core v2.0 (дорожная карта после пилота)
> **Последнее обновление**: 2026-11-17

---

## 🎯 Трек A: Пилот у владельца (meeting-first)

Ре-анкор на две задачи с встречи 11.11: **оптимизация обеспечения заказа** (себестоимость) и **синхронизация отделов** («цифровой бегунок»). Промышленная ОС v2.0 — дорожная карта после подтверждения экономии на реальных данных.

| Артефакт / шаг | Статус | Ссылка |
|---|---|---|
| План пилота (MVP-1 закупки, MVP-2 бегунок) | ✅ Готов | [`docs/plans/2026-11-14-pilot-track-a.md`](docs/plans/2026-11-14-pilot-track-a.md) |
| Пилотный демо-презент для владельца | ✅ Готов | [`01_Дирекция/Пилотный_демо_презент_Makota_AI.md`](01_Дирекция/Пилотный_демо_презент_Makota_AI.md) |
| Интерактивный симулятор и дашборд | ✅ Готов | [`reports/makota_interactive_dashboard.html`](reports/makota_interactive_dashboard.html) |
| Сквозной воркфлоу расчета КП | ✅ Готов | [`specs/workflows/cost_optimization_and_rfp_workflow.md`](specs/workflows/cost_optimization_and_rfp_workflow.md) |
| Конфиги ИИ-агентов (JSON Schemas) | ✅ Готовы | [`specs/agents/cost_engineer_agent_config.json`](specs/agents/cost_engineer_agent_config.json) |
| Бенчмарки и разбор кейсов (Paperless/Sandvik) | ✅ Готов | [`docs/BENCHMARKS_AND_CASE_STUDIES.md`](docs/BENCHMARKS_AND_CASE_STUDIES.md) |
| Письмо владельцу с видением | 🟡 Черновик на проверку | [`reports/owner_email_draft.md`](reports/owner_email_draft.md) |
| Запрос данных (тендеры, заказы, прайсы) | ✅ Готов к отправке | [`reports/data_request.md`](reports/data_request.md) |
| Данные от владельца | ⏳ Ожидаются | блокирует MVP-1 и MVP-2 |
| Визит на производство | ⏳ Не согласован | нужен для обоих MVP |
| Материалы к визиту (интервью-гайд, чеклист, service blueprint) | ✅ Готовы | [`docs/visit/`](docs/visit/interview-guide.md) |
| Пакет собственника 17.11: бриф, финмодель, атлас 130 workflow | 📚 Справочник. Суммы демонстрационные, трек A не заменяет | [`01_Дирекция/Пакет_собственника_2026-11-17/00_Оглавление.md`](01_Дирекция/Пакет_собственника_2026-11-17/00_Оглавление.md) |
| MVP-1: пулинг закупок + разбор тендеров | ⏳ Ждёт данные | [`specs/agents/procurement_pool_spec.md`](specs/agents/procurement_pool_spec.md) |
| MVP-2: Order Controller на 3–5 заказах | ⏳ Ждёт данные | [`specs/agents/order_controller_spec.md`](specs/agents/order_controller_spec.md), слой данных: vault `02_Продажи_и_Заказы` |

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

> [!CAUTION]
> **Модельные оценки, не верифицированы.** Все цифры ниже рассчитаны из гипотетических входов `founder/numbers.json` и не подтверждены реальными данными владельца. Цены поставщиков, спрос и чеки требуют проверки. Использовать только как ориентир для обсуждения, не как факт.

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
