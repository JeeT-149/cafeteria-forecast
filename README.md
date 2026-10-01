# Cafeteria Order Data: Analysis & 7-Day Forecast

An end-to-end data engineering, EDA, and forecasting pipeline for over 5.3 million cafeteria orders.

## Results at a Glance

![Executive Dashboard](reports/figures/00_executive_dashboard.png)

## What I Built

- **SQL Extraction**: Streamed and isolated 7 critical tables out of an 11 GB MySQL dump.
- **Cleaning**: Built an automated data cleaning funnel removing partial-year records and empty branches, filtering down to forecast-valid paid orders.
- **EDA**: Analyzed hourly patterns, branch distributions, payment methods, and non-positive total anomalies.
- **Forecasting**: Evaluated multiple models via 8-fold rolling backtesting, selecting a robust baseline (median of last 4 same weekdays) for the next 7 days.
- **Validation**: Programmatic verification of all report documentation against pipeline output.

## Key Findings

- **Volume Concentration**: Branches 1 and 2 account for 80.1% of all valid orders.
- **Peak Hours**: 51% of daily demand is concentrated in just 5 hours (13, 14, 16, 17, 18).
- **Weekend Drop-off**: Weekends average only about 6.6% of weekday volume.
- **Digital Payments**: Digital modes dominate, with Paytm representing 39.6% of orders.
- **Quality Anomalies**: 96,199 mobile-app orders flagged with zero or non-positive totals, mostly concentrated in Nov-Dec 2024.

## Forecast

![Forecast Dashboard](reports/figures/10_forecast_dashboard.png)

## Repository Structure

| Path | Purpose |
|---|---|
| `docs/` | Detailed documentation on assumptions, cleaning logs, and methodology |
| `reports/` | Output dashboards, charts, and facts json |
| `src/` | Data extraction, cleaning pipeline, EDA, and forecasting scripts |
| `data/processed/` | Processed result datasets |
| `report.md` | Full analytical report |

## Reproduce

The raw dump is not in the repo (11 GB). Place `Cafeteria Order Data.sql` in `data/`.
```powershell
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
python src/extract_tables.py            # -> data/interim/tables/*.sql
python src/fix_sql_terminators.py
docker run --name cafe-db -e MYSQL_ROOT_PASSWORD=pass -e MYSQL_DATABASE=cafe -p 3306:3306 `
  -v "${PWD}/data/interim/tables:/tables" -d mysql:8 --sql-mode="NO_ENGINE_SUBSTITUTION" `
  --innodb-buffer-pool-size=2G --innodb-flush-log-at-trx-commit=2 --max_allowed_packet=1G --skip-log-bin
foreach ($t in "branches","counters","dishes","categories","order_has_statuses","orders","order_details") {
  docker exec cafe-db sh -c "mysql -uroot -ppass cafe < /tables/$t.sql" }
# then add indexes: orders(order_date), orders(branch_id, order_date), orders(counter_id), order_details(order_id)
python src/clean.py
python src/top_items.py
python src/eda.py
python src/forecast_extra.py 2 1
python src/audit_docs.py
```
Database credentials are local-only defaults for a throwaway container. The analysis re-runs from `data/processed/` CSVs without the database.

## Documentation

- [report.md](report.md)
- [docs/README.md](docs/README.md)
- [docs/assumptions.md](docs/assumptions.md)
- [docs/02_cleaning_log.md](docs/02_cleaning_log.md)
- [docs/04_forecast_method.md](docs/04_forecast_method.md)
- [docs/05_model_evaluation.md](docs/05_model_evaluation.md)

## Privacy

`users.sql` contains personal data (emails, password hashes, OTPs). It was not analysed and is not committed.