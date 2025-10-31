'''
Data retrieval API routes, including endpoints for data collection and retrieval.
This module defines data flow from smartphone devices to the backend server
'''

import os

from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Any
from src.logging.logging import logging
from src.api.controller.db_controller import create_supabase_connection

from dotenv import load_dotenv
load_dotenv()

# Define SUPABASE constants
URL = os.getenv("SUPABASE_API_URL")
API_KEY = os.getenv("SUPABASE_API_KEY")

# Define router instance
router = APIRouter()

# Define data retrieval route
@router.post("/raw-metrics", status_code=200)
async def get_data_from_smartphone(request: Request) -> Dict[str, Any]:
  '''
  Endpoint to retrieve data from smartphone devices based on the specified table name.
  '''
  try:
    # Define request payload
    logging.info("Parsing request payload...")
    payload = await request.json()
    
    # Check if device_id is present in payload
    if "device_id" not in payload:
      raise HTTPException(status_code=400, detail="Missing 'device_id' in request payload!")
    
    # Create supabase connection
    logging.info("Creating Supabase connection...")
    supabase = create_supabase_connection()
    
    # Look for user_id based on device_id
    logging.info("Looking for user_id based on device_id...")
    device_id = payload["device_id"]
    user_id = None
    
    logging.info(f"Fetching user_id for device_id: {device_id}...")
    try:
      if device_id:
        row = (
          supabase.table("devices")
          .select("user_id")
          .eq("device_id", device_id)
          .maybe_single()
          .execute()
        )
        if row.data and row.data.get("user_id"):
          user_id = row.data["user_id"]
    except Exception:
      pass
    
    # Insert user_id to payload if found
    if user_id:
      payload["user_id"] = user_id
    
    # Check if there is not SUPABASE credentials
    if not URL or not API_KEY:
      raise HTTPException(status_code=500, detail="Supabase credentials are not set properly!")
    
    # Insert data to supabase
    logging.info("Inserting data to Supabase...")
    response = supabase.table("raw_metrics").insert(payload).execute()
    
    # Return success response
    return {
      "ok": True,
      "message": "Data has been retrieved successfully",
    }
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))