'''
Data acquisition API routes, including endpoints for data collection and retrieval.
This module defines data flow from smartphone devices to the backend server
'''
import os
import sys

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from src.logging.logging import logging
from src.api.controller.db_controller import create_supabase_connection 
from src.api.model.raw_metrics import RawMetricsResponse
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation
from src.service.metrics_calculation import MetricsCalculation

# Define router instance
router = APIRouter()

# Define data retrieval route
@router.get("/raw-metrics", status_code=200, response_model=RawMetricsResponse)
async def visualize_data_from_smartphone(
  table_name:str = Query(..., description="Fetch latest record for specific table_name"),
  device_id:str = Query(..., description="Device ID to filter data")) -> RawMetricsResponse:
  try:
    # Create throuhgput metrics
    ingestion = DataIngestion(table_name=table_name, device_id=device_id)
    df_raw = ingestion.extract_data_from_db(limit=10)
    
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
    df_raw = df_raw.sort_values(by="created_at")
    latest_raw = df_raw.iloc[-1].to_dict()
    
    # Check if transformed data is not empty
    latest_thr_dict = None
    if not transformed.empty:
      transformed = transformed.sort_values("created_at")
      latest_thr_dict = transformed.iloc[-1].to_dict()
      
      latest_thr_dict = {
        "device_id": latest_thr_dict["device_id"],
        "created_at": latest_thr_dict["created_at"].isoformat(),
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