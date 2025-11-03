'''
Graphs Visualization Routes Module
This module defines the API routes for visualizing graphs based on throughput metrics.
'''
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from src.logging.logging import logging
from src.api.model.graphs_model import ThroughputHistoryResponse, ThroughputPoint
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation

# Define router instance
router = APIRouter()

# Define throughput history route
@router.get("/metrics/throughput", status_code=200, response_model=ThroughputHistoryResponse)
async def get_throughput_history(
  device_id: str = Query(..., description="Device ID"),
  limit: int = Query(1000, ge=10, le=5000, description="Data fetch limit")) -> ThroughputHistoryResponse:
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
        "points": []
      }
    
    # Calculate throughput
    df_throughput = DataTransformation(data=df_raw).compute_throughput()
    
    # Check if throughput data is empty
    if df_throughput.empty:
      return {
        "device_id": device_id,
        "points": []
      }
    
    # Exclude null values
    df_throughput = df_throughput.dropna(subset=["throughput_total_mbps"])
    df_throughput = df_throughput[df_throughput["throughput_total_mbps"] >= 0]
    df_throughput = df_throughput.sort_values("created_at")
    
    # Define data points
    points = []
    for _, row in df_throughput.iterrows():
      points.append(
        ThroughputPoint(
          timestamp=row["created_at"],
          throughput_total_mbps=float(row["throughput_total_mbps"]),
          throughput_upload_mbps=float(row["throughput_upload_mbps"]),
          throughput_download_mbps=float(row["throughput_download_mbps"])
        )
      )
    
    # Return response
    return {
      "message": "Throughput history retrieved successfully",
      "device_id": device_id,
      "points": points
    }
  except Exception as e:
    logging.error(f"Error in get_throughput_history: {e}")
    raise HTTPException(status_code=500, detail=str(e))