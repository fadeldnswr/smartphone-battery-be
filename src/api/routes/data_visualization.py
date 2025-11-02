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

# Define router instance
router = APIRouter()

# Define data retrieval route
@router.get("/raw-metrics", status_code=200, response_model=RawMetricsResponse)
async def visualize_data_from_smartphone(
  table_name:str = Query(..., description="Fetch latest record for specific table_name"),
  device_id:str = Query(..., description="Device ID to filter data")) -> RawMetricsResponse:
  try:
    logging.info("Get data from database..")
    supabase = create_supabase_connection()
    
    # Fetch last raw data from specified table
    logging.info(f"Fetching raw data from table: {table_name}...")
    raw_data_response = (
      supabase.table(table_name=table_name)
      .select("*")
      .eq("device_id", device_id)
      .order("created_at", desc=True)
      .limit(1)
      .execute()
    )
    
    logging.info("Data retrieved successfully.")
    return {
      "message": "Data has been retrieved successfully",
      "data": raw_data_response.data
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))