# Model Evaluation

Validation method: 8 rolling-origin folds, 7-day horizon, chronological validation.
Model selection uses the lowest validation MAE. MAE and WAPE are emphasized, and MAPE is not used because very low-volume days make percentage errors unstable.

| Branch | Model | MAE | RMSE | WAPE | bias |
|---|---|---|---|---|---|
| 2 | median_last_4_same_weekday | 447.2 | 1120.9 | 6.9% | -302.9 |
| 2 | seasonal_naive | 607.1 | 1323.9 | 9.4% | -156.9 |
| 2 | holt_winters | 768.7 | 1196.8 | 11.9% | 6.9 |
| 1 | median_last_4_same_weekday | 406.7 | 1108.8 | 6.7% | -288.6 |

Selected model for both branches: `median_last_4_same_weekday`.
