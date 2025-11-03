'''
Graphs Visualization Routes Module
This module defines the API routes for visualizing graphs based on throughput metrics.
'''
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from src.logging.logging import logging
from src.api.model.graphs_model import GraphsHistoryResponse, ThroughputPoint, EnergyConsumptionPoint
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation

# Define router instance
router = APIRouter()

# Define throughput history route
@router.get("/metrics", status_code=200, response_model=GraphsHistoryResponse)
async def get_throughput_history(
  device_id: str = Query(..., description="Device ID"),
  limit: int = Query(1000, ge=10, le=5000, description="Data fetch limit")) -> GraphsHistoryResponse:
  '''
  Function to retrieve throughput history for graph visualization.\n
  params:
  - device_id: Device ID to filter data.
  - limit: Number of data points to retrieve.\n
  returns:
  
  '''
  try:
    # Define data ingestion
    df_raw = DataIngestion(table_name="raw_metrics", device_id=device_id).extract_data_from_db(limit=limit)
    
    # Check if data is empty
    if df_raw.empty:
      return {
        "device_id": device_id,
        "thr_points": [],
        "energy_points": []
      }
    
    # Calculate throughput
    df_metrics = DataTransformation(data=df_raw).compute_metrics()
    
    # Check if throughput data is empty
    if df_metrics.empty:
      return {
        "device_id": device_id,
        "thr_points": [],
        "energy_points": []
      }
    
    # Create datetime column
    df_metrics["created_at"] = pd.to_datetime(df_metrics["created_at"])
    df_metrics = df_metrics.sort_values("created_at")
    
    # Prepare data points for throughput
    if "throughput_total_mbps" in df_metrics.columns:
      df_thr = df_metrics.dropna(subset=["throughput_total_mbps"])
      df_thr = df_thr[df_thr["throughput_total_mbps"] >= 0]
    else:
      df_thr = pd.DataFrame()
    
    # Define throughput data points
    thr_points = []
    # Check if df_thr is not empty
    if not df_thr.empty:
      for _, row in df_thr.iterrows():
        thr_points.append(
          ThroughputPoint(
            timestamp=row["created_at"],
            throughput_total_mbps=float(row["throughput_total_mbps"]),
            throughput_upload_mbps=float(row.get("throughput_upload_mbps", 0.0)),
            throughput_download_mbps=float(row.get("throughput_download_mbps", 0.0))
          )
        )
    
    # Define energy consumption data points
    energy_points = []
    # Check if energy_wh column exists
    if "energy_wh" in df_metrics.columns:
      df_energy = df_metrics.dropna(subset=["energy_wh"])
      for _, row in df_energy.iterrows():
        energy_points.append(
          EnergyConsumptionPoint(
            timestamp=row["created_at"],
            energy_wh=float(row["energy_wh"])
          )
        )
    
    # Return response
    return {
      "message": "Throughput history retrieved successfully",
      "device_id": device_id,
      "thr_points": thr_points,
      "energy_points": energy_points
    }
  except Exception as e:
    logging.error(f"Error in get_throughput_history: {e}")
    raise HTTPException(status_code=500, detail=str(e))