# Makota

Проект валидации, юнит-экономики и запуска бизнес-направлений Makota.

## Установленный стек: Founder Skill Suite

В проект интегрирован пакет из 11 взаимосвязанных навыков для стресс-тестирования бизнеса перед запуском:

| Команда / Навык | Роль | Назначение |
| --- | --- | --- |
| `/founder-board` | Совет директоров | 3 субагента по фреймворкам: Алекс Гормози (*$100M Offers*), Питер Тиль (*Zero to One*), Стив Джобс (*Steve Jobs*). Оценка, риски, вердикт. |
| `/founder-competitors` | Разведчик конкурентов | Карта прямых/косвенных конкурентов и субститутов с ценами, позиционированием и жалобами клиентов. |
| `/founder-consumer` | Панель покупателей | Рой из 100 покупательских персон (субагентов). Прогон оффера через 100 сценариев покупки с фиксацией возражений и причин отказов. |
| `/founder-pricing` | Стратег ценообразования | Анализ чувствительности цен Ван Вестендорпа (Van Westendorp PSM): PMC, PME, OPP, IPP. |
| `/founder-offer` | Архитектор оффера | Стек ценности (бонусы, гарантии, срочность, нейминг) для снятия возражений покупательской панели. |
| `/founder-cfo` | Финансовый директор (CFO) | Юнит-экономика: маржа, точка безубыточности (break-even), помесячный прогноз 1-го года, окупаемость стартовых инвестиций, what-if сценарии. |
| `/founder-marketing` | Директор по маркетингу | Позиционирование, каналы привлечения, 30-дневная кампания запуска, 10 хуков, предельная стоимость клиента (CAC cap). |
| `/founder-brand` | Бренд-дизайнер | Нейминг, проверка торговых марок/доменов, Tone of Voice, обещание бренда и гайдлайны. |
| `/founder-ops` | Операционный директор | Поставщики, штат, регламенты дня запуска, софт, разрешения, реестр операционных рисков. |
| `/founder-launch` | Лид запуска | Дешёвый полевой тест, обратный отсчёт запуска, регламент первого дня и первые 30 дней работы. |
| `/founder-plan` | Бизнес-планировщик | Сборка единого бизнес-плана `founder/business-plan.md` с детерминированным расчётом вердикта (`Profitable`, `Not yet`, `Incomplete`). |

---

## Порядок запуска пайплайна

Каждый этап опирается на данные предыдущих и сохраняет артефакты в папку `founder/`:

```
board ➔ competitors ➔ consumer ➔ pricing ➔ offer ➔ cfo ➔ marketing ➔ brand ➔ ops ➔ launch ➔ plan
```

1. `founder/idea.md` (входная точка: продукт, клиент, ценник, гео/доставка, ограничения)
2. `founder/competitors.md`
3. `founder/customer.json` + `founder/pitch.md` ➔ `founder/panel/`
4. `founder/pricing-curve.md`
5. `founder/offer.md`
6. `founder/numbers.json` ➔ `founder/cfo.md`
7. `founder/marketing.md`
8. `founder/brand.md`
9. `founder/ops.md`
10. `founder/launch.md`
11. `founder/business-plan.md`

---

## Архитектура интеграции в Makota

- **Antigravity Workspace:** `.agents/skills/founder-*` (локальные проектные навыки)
- **Claude Code Workspace:** `.claude/skills` (симлинк на `.agents/skills`)
- **Direct CLI & Tools:** `skills/` (симлинк на `.agents/skills`)
- **Global Antigravity Catalog:** `~/.gemini/config/skills/founder-*` (доступно во всех проектах)
- **Manifests:** `.claude-plugin/plugin.json` и `.claude-plugin/marketplace.json`
- **Tests:** `python3 -m unittest discover -s tests -v` (29 тестов, 100% pass)

---

## Быстрый запуск утилит (Python 3.8+, no external dependencies)

```bash
# Расчет юнит-экономики (CFO)
python3 skills/founder-cfo/unit_economics.py skills/founder-cfo/example.json

# Инициализация панели покупателей (100 персон)
python3 skills/founder-consumer/panel.py init --customer founder/customer.json --pitch founder/pitch.md

# Анализ ценовой чувствительности
python3 skills/founder-pricing/van_westendorp.py founder/panel/answers --price 6.50

# Компиляция итогового бизнес-плана
python3 skills/founder-plan/compile.py --dir founder
```
