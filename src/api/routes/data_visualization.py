'''
Data acquisition API routes, including endpoints for data collection and retrieval.
This module defines data flow from smartphone devices to the backend server
'''
import os
import sys
import pandas as pd

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from src.logging.logging import logging
from src.api.model.raw_metrics import RawMetricsResponse
from src.api.model.usage_app_models import AppUsageResponse
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation

# Define router instance
router = APIRouter()

# Define data retrieval route
@router.get("/raw-metrics", status_code=200, response_model=RawMetricsResponse)
async def visualize_data_from_smartphone(
  table_name:str = Query(..., description="Fetch latest record for specific table_name"),
  device_id:str = Query(..., description="Device ID to filter data")) -> RawMetricsResponse:
  '''
  Function to get raw metrics data from smartphone devices.\n
  params:
  - table_name : str : Table name to filter data\n
  - device_id : str : Device ID to filter data\n
  returns:
  - RawMetricsResponse : Response model containing raw metrics data
  '''
  try:
    # Create throuhgput metrics
    ingestion = DataIngestion(table_name=table_name, device_id=device_id)
    df_raw = ingestion.extract_data_from_db(limit=10)
    
    # Check if data is empty
    if df_raw.empty:
      return {
        "message": "No data has been found",
        "data": [],
        "throughput": []
      }
    transformed = DataTransformation(data=df_raw).compute_throughput()
    logging.info(f"Transformed data type: {type(transformed)}")
    logging.info(f"Transformed data shape: {transformed.shape}")
    
    # Take last record of transformed data
    df_raw["ts_utc"] = pd.to_datetime(df_raw["ts_utc"]) 
    df_raw = df_raw.sort_values(by="ts_utc")
    latest_raw = df_raw.iloc[-1].to_dict()
    
    # Check if transformed data is not empty
    latest_thr_dict = None
    if not transformed.empty:
      transformed = transformed.sort_values("ts_utc")
      latest_thr_dict = transformed.iloc[-1].to_dict()
      latest_thr_dict = {
        "device_id": latest_thr_dict["device_id"],
        "ts_utc": latest_thr_dict["ts_utc"],
        "throughput_upload_mbps": float(latest_thr_dict["throughput_upload_mbps"]),
        "throughput_download_mbps": float(latest_thr_dict["throughput_download_mbps"]),
        "throughput_total_mbps": float(latest_thr_dict["throughput_total_mbps"]),
      }
    
    # Return responses
    logging.info("Data retrieved successfully.")
    return {
      "message": "Data has been retrieved successfully",
      "data": [latest_raw],
      "throughput": [latest_thr_dict] if latest_thr_dict else []
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# Define data retrieval route for application usage statistics
@router.get("/app-usage", status_code=200, response_model=AppUsageResponse)
async def get_app_usage_stats(
  device_id:str = Query(..., description="Device ID to filter data"),
  top_rank:int = Query(4, description="Number of top applications to consider for usage statistics"),
  table_name:str = Query("raw_metrics", description="Table name to filter data")
  ) -> AppUsageResponse:
  '''
  Function to get application usage statistics for a specific device.\n
  params:
  - device_id : str : Device ID to filter data\n
  - top_rank : int : Number of top applications to consider for usage statistics\n
  returns:
  - AppUsageResponse : Response model containing application usage statistics
  '''
  try:
    # Ingest raw data
    ingestion = DataIngestion(table_name=table_name, device_id=device_id)
    df_raw = ingestion.extract_data_from_db(limit=200)
    
    # Check if data is empty
    if df_raw.empty:
      return {
        "device_id": device_id,
        "usage_stats": []
      }
    
    # Compute application usage statistics
    usage_df = DataTransformation(data=df_raw).compute_usage_application(top_rank=top_rank)
    if usage_df.empty:
      return {
        "device_id": device_id,
        "usage_stats": []
      }
    
    # Return usage statistics
    usage_stats = []
    for _, row in usage_df.iterrows():
      usage_stats.append({
        "device_id": row["device_id"],
        "fg_pkg": row["fg_pkg"],
        "total_mb": float(row["total_mb"]),
        "avg_throughput_mbps": float(row["avg_throughput_mbps"]),
        "rank": int(row["rank"])
      })

    # Return response
    return {
      "device_id": device_id,
      "usage_stats": usage_stats if usage_stats else []
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))