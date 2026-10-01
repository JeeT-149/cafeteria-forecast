# Forecast Method

## Objective
Forecast the next 7 days of daily valid paid order count.
Forecast dates: 2025-04-01 through 2025-04-07.

## Target
FY window + branch not in (-1,3,11) + `paid_or_cancel = paid` + `grand_total > 0`

## Branch 2
2,178,801 valid paid orders.
365 daily observations.
2024-04-01 through 2025-03-31.

## Validation
Use 8 rolling-origin folds, 7-day horizon, chronological validation.

## Models
* Seasonal Naive
* Median of last 4 same weekdays
* Holt-Winters

## Branch 2 v2 metrics
`median_last_4_same_weekday`
* MAE = 447.2
* RMSE = 1120.9
* WAPE = 6.9%
* bias = -302.9

`seasonal_naive`
* MAE = 607.1
* RMSE = 1323.9
* WAPE = 9.4%
* bias = -156.9

`holt_winters`
* MAE = 768.7
* RMSE = 1196.8
* WAPE = 11.9%
* bias = 6.9

Selection rule: lowest validation MAE.
Selected model: `median_last_4_same_weekday`.
RMSE gives a different ordering because it weights large errors more heavily.

## Branch 2 forecast
| date | forecast | lower_80 | upper_80 |
|---|---|---|---|
| 2025-04-01 | 9914 | 9454 | 10374 |
| 2025-04-02 | 9632 | 9172 | 10092 |
| 2025-04-03 | 9363 | 8902 | 9824 |
| 2025-04-04 | 7530 | 7070 | 7990 |
| 2025-04-05 | 655 | 194 | 1116 |
| 2025-04-06 | 200 | 0 | 660 |
| 2025-04-07 | 8666 | 8206 | 9126 |

These are empirical 80% intervals derived from backtest absolute errors.

## Branch 1 robustness check
2,095,347 valid paid orders.
365 observations.

`median_last_4_same_weekday`
* MAE: 406.7
* RMSE: 1108.8
* WAPE: 6.7%
* bias: -288.6

It was also selected using lowest MAE.

## MAPE
MAPE was dropped as the primary metric because very low-volume days make percentage errors unstable. MAE and WAPE are the practical primary metrics.

## Limitations
* one financial year only
* no year-over-year seasonality
* no external features such as promotions, weather, holidays, or events
* forecast is short horizon
* intervals are empirical, not model-derived
* estimates are not guarantees
