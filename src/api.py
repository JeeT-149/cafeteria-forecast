from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
import os

app = FastAPI(title="Cafeteria Forecast API")

P = Path("data/processed")

class ForecastResponse(BaseModel):
    branch: int
    target: str
    ranges: str
    forecast: list[dict]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/forecast", response_model=ForecastResponse)
def get_forecast(branch: int):
    if branch not in [1, 2]:
        raise HTTPException(status_code=404, detail=f"Forecast for branch {branch} not supported.")
    
    file_path = Path("reports/final_outputs") / f"forecast_branch_{branch}.csv"
    if not file_path.exists():
        raise HTTPException(status_code=500, detail="Required analysis outputs are not present. Run the documented data-processing pipeline first.")
    
    try:
        df = pd.read_csv(file_path)
        # Identify the date column (it's the first column, usually unnamed)
        date_col = df.columns[0]
        
        forecast_list = []
        for _, row in df.iterrows():
            forecast_list.append({
                "date": str(row[date_col]),
                "forecast_orders": float(row.get('forecast_orders', 0)),
                "lower_80": float(row.get('lower_80', 0)),
                "upper_80": float(row.get('upper_80', 0)),
                "model": str(row.get('model', ''))
            })
            
        return ForecastResponse(
            branch=branch,
            target="valid paid orders per day",
            ranges="empirical 80%, from backtest errors",
            forecast=forecast_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
