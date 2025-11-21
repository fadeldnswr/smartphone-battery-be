'''
Route and logic for prediction endpoints
'''
import os
import sys

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from src.logging.logging import logging
from src.api.model.prediction_model import PredictionResponse
from src.api.controller.prediction_controller import run_prediction_pipeline

# Define router instance
router = APIRouter()

# Define prediction endpoint
@router.get("/soh", status_code=200, response_model=PredictionResponse)
async def get_prediction(device_id: str = Query(..., description="Device ID")) -> PredictionResponse:
  try:
    result = run_prediction_pipeline(device_id=device_id)
    return PredictionResponse(
      message=result.message,
      device_id=result.device_id,
      soh_pred_pct=result.soh_pred_pct,
      soh_pred=result.soh_pred,
      rul_cycles=result.rul_cycles,
      rul_months=result.rul_months,
      rul_hours=result.rul_hours,
      soh_series=result.soh_series
    )
  except Exception as e:
    logging.error(f"Error in prediction endpoint: {e}")
    raise HTTPException(status_code=500, detail=f"Error in prediction endpoint: {e}")