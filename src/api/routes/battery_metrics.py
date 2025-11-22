'''
Battery metrics API routes to visualize collected battery data from smartphone devices.
This module defines data flow from smartphone devices to the backend server.
'''

import pandas as pd
import numpy as np
import os
import sys

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from src.logging.logging import logging
from src.api.model.battery_models import BatteryMetricsResponse
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation
from src.api.controller.prediction_controller import safe_float

# Define router instance
router = APIRouter()

# Define battery metrics retrieval route
@router.get("/metrics", status_code=200, response_model=BatteryMetricsResponse)
async def get_battery_metrics(
  device_id: str = Query(..., description="Device ID for user devices"),
  table_name: str = Query(..., description="Table name to retrieve data from")) -> BatteryMetricsResponse:
  '''
  Function to calculate and send battery metrics data for visualization.\n
  params:
  - device_id: Device ID to filter data.\n
  returns:
  - BatteryMetricsResponse: Response model containing battery metrics data.
  '''
  try:
    # Create dataframe from pipeline
    df_raw = DataIngestion(table_name=table_name, device_id=device_id).extract_data_from_db(limit=1000)
    if df_raw.empty:
      return {
        "device_id": device_id,
        "soh_data": [],
        "cycles_data": [],
      }
    
    # Calculate battery metrics
    df_metrics = DataTransformation(data=df_raw).compute_metrics()
    if df_metrics.empty:
      return {
        "device_id": device_id,
        "soh_data": [],
        "cycles_data": [],
      }
    
    # Create datetime column
    df_metrics["created_at"] = pd.to_datetime(df_metrics["created_at"])
    if "ts_utc" in df_metrics.columns:
      df_metrics["ts_utc"] = pd.to_datetime(df_metrics["ts_utc"])
      df_metrics = df_metrics.sort_values("ts_utc")
    else:
      df_metrics = df_metrics.sort_values("created_at")
    
    # Create list of numerical cols for data sanitation
    numerical_cols = [
      "Q_mAh", "Ct_mAh", "soh_pct", "soh_smooth", 
      "delta_Q_mAh", "discharge_mAh", "EFC"
    ]
    required_cols = ["device_id", "created_at"] + numerical_cols
    available_soh_cols = [col for col in required_cols if col in df_metrics.columns]
    df_soh = df_metrics[available_soh_cols].copy()
    
    # Clean inf and NaN
    df_soh = df_soh.replace([np.inf, -np.inf], np.nan)
    if "soh_pct" in df_soh.columns:
      df_soh = df_soh.dropna(subset=["soh_pct"])
    
    for col in ["Q_mAh", "Ct_mAh"]:
      if col in df_soh.columns:
        df_soh[col] = df_soh[col].fillna(0.0)
    
    df_soh = df_soh.tail(1000)
    
    # Check if soh_df is empty
    if df_soh.empty:
      return {
        "device_id": device_id,
        "soh_data": [],
        "cycles_data": [],
      }
    
    
    # Take 100 last SoH data points
    soh_data = []
    for _, row in df_soh.iterrows():
      soh_data.append({
        "device_id": row["device_id"],
        "created_at": row["created_at"],
        "Q_mAh": safe_float(row["Q_mAh"], 0.0, field="Q_mAh"),
        "Ct_mAh": safe_float(row["Ct_mAh"], 0.0, field="Ct_mAh"),
        "soh_pct": safe_float(row["soh_pct"], 0.0, field="soh_pct"),
      })
    
    # Take latest data from metrics
    latest = df_metrics.iloc[-1]
    cycles_data = [{
      "device_id": latest["device_id"],
      "created_at": latest["created_at"].isoformat() if pd.notna(latest["created_at"]) else None,
      "delta_charge_uah": safe_float(latest.get("delta_Q_mAh"), 0.0, field="delta_charge_uah"),
      "discharge_uah": safe_float(latest.get("discharge_mAh"), 0.0, field="discharge_uah"),
      "cycles_est": safe_float(latest.get("EFC"), 0.0, field="EFC"),
    }]
    # Return battery metrics response
    return {
      "device_id": device_id,
      "soh_data": soh_data,
      "cycles_data": cycles_data,
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error retrieving battery metrics: {e}")