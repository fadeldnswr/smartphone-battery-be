'''
Data retrieval API routes, including endpoints for data collection and retrieval.
This module defines data flow from smartphone devices to the backend server
'''

from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Any
from src.logging.logging import logging

import httpx
import os

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
    payload = await request.json()
    
    # Check if there is not SUPABASE credentials
    if not URL or not API_KEY:
      raise HTTPException(status_code=500, detail="Supabase credentials are not set properly!")
    
    # Validate payload
    if "device_id" not in payload:
      raise HTTPException(status_code=400, detail="Missing 'device_id' in request payload!")
    
    # Make async request to Supabase to fetch data
    async with httpx.AsyncClient() as client:
      response = await client.post(
        url=f"{URL}/rest/v1/raw_metrics",
        headers={
          "apiKey": API_KEY,
          "Authorization": f"Bearer {API_KEY}",
          "Prefer": "return=minimal",
          "Content-Type": "application/json"
        },
        json=payload,
        timeout=10.0
      )
      
      # If not successful, raise HTTP exception
      if response.status_code not in (200, 201, 204):
        detail = response.text
        raise HTTPException(status_code=response.status_code, detail=f"Supabase error: {detail}")
    return {
      "ok": True,
      "message": "Data has been retrieved successfully",
    }
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))