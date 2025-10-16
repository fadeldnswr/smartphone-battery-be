'''
Data acquisition API routes, including endpoints for data collection and retrieval.
This module defines data flow from smartphone devices to the backend server
'''
import os
import sys

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.logging.logging import logging
from src.api.controller.db_controller import get_data_from_db

# Define router instance
router = APIRouter()

# Define data retrieval route
@router.get("/metrics", status_code=200)
async def visualize_data_from_smartphone() -> Dict[List, Any]:
  try:
    logging.info("Get data from database..")
    raw_data = get_data_from_db()
    
    logging.info("Data retrieved successfully.")
    return {
      "message": "Data has been retrieved successfully",
      "data": raw_data
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))