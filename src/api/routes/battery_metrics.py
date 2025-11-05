'''
Battery metrics API routes to visualize collected battery data from smartphone devices.
This module defines data flow from smartphone devices to the backend server.
'''

import pandas as pd
import os
import sys

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from src.logging.logging import logging
from src.api.model.battery_models import BatteryMetricsResponse
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation

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
    df_metrics = df_metrics.sort_values("created_at")
    
    # Take last record of battery cycles and State of Health (SoH)
    df_metrics["ts_utc"] = pd.to_datetime(df_metrics["ts_utc"])
    df_metrics = df_metrics.sort_values("ts_utc")
    latest_data = df_metrics.iloc[-1].to_dict()
    
    # Return battery metrics response
    return {
      "device_id": device_id,
      "soh_data": [
        {
          "device_id": latest_data["device_id"],
          "created_at": latest_data["created_at"],
          "Q_mAh": float(latest_data["Q_mAh"]),
          "Ct_mAh": float(latest_data["Ct_mAh"]),
          "soh_pct": float(latest_data["soh_pct"]),
        }
      ],
      "cycles_data": [
        {
          "device_id": latest_data["device_id"],
          "created_at": latest_data["created_at"],
          "delta_charge_uah": float(latest_data["delta_charge_uah"]),
          "discharge_uah": float(latest_data["discharge_uah"]),
          "cycles_est": float(latest_data["cycles_est"]),
        }
      ]
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error retrieving battery metrics: {e}")