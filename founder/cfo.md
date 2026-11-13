# Unit economics: Makota — ИИ-диспетчер заказов для производственного предприятия

Every number below comes from the input file. Nothing is looked up or guessed.

## One контракт (обработанная заявка с КП)

| line | per контракт (обработанная заявка с КП) |
| --- | ---: |
| Price | $15,000.00 |
| Стоимость металлопроката/комплектующих (себестоимость заказа) | -$11,500.00 |
| Транспорт и логистика (% от заказа) | -$1,200.00 |
| Операционные расходы агента (AI API tokens, ~$2/заказ) | -$150.00 |
| Комиссия платежной системы (1%) | -$150.00 |
| **Contribution** (what each контракт (обработанная заявка с КП) leaves to pay the fixed costs) | **$2,000.00** (13%) |

## The margin that matters

Fixed costs: $160,000 a month (ИИ-подписки (Claude/GPT/Antigravity ~$200) $20,000, Аренда офиса (доля) $50,000, Менеджер по работе с заявками (1 чел.) $80,000, Прочие SaaS и инфраструктура $10,000).

- **Break-even: 4 контракт (обработанная заявка с КП)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (8 a day): **7%** of every sale, after every cost.
- Capacity: 20 a day.

## Year 1, month by month

| month | контракт (обработанная заявка с КП)s a day | revenue | profit | cumulative (after $200,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | $2,640,000 | $192,000 | -$8,000 |
| 2 | 8 | $2,640,000 | $192,000 | $184,000 |
| 3 | 8 | $2,640,000 | $192,000 | $376,000 |
| 4 | 8 | $2,640,000 | $192,000 | $568,000 |
| 5 | 8 | $2,640,000 | $192,000 | $760,000 |
| 6 | 8 | $2,640,000 | $192,000 | $952,000 |
| 7 | 8 | $2,640,000 | $192,000 | $1,144,000 |
| 8 | 8 | $2,640,000 | $192,000 | $1,336,000 |
| 9 | 8 | $2,640,000 | $192,000 | $1,528,000 |
| 10 | 8 | $2,640,000 | $192,000 | $1,720,000 |
| 11 | 8 | $2,640,000 | $192,000 | $1,912,000 |
| 12 | 8 | $2,640,000 | $192,000 | $2,104,000 |

- **Year 1 operating profit: $2,304,000** on $31,680,000 of revenue.
- After the $200,000 startup spend: $2,104,000.
- Startup money earned back: month 2.
- Cash you need before it pays for itself: **$200,000**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 7% | 4 | $2,304,000 |
| Price -10% | -3% | 15 | -$864,000 |
| Volume -20% | 6% | 4 | $1,459,200 |
| Unit costs +15% | -6% | 146 | -$1,814,400 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
