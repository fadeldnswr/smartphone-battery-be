'''
Models for prediction visualization API responses.
'''
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# Define prediction response model
class PredictionResponse(BaseModel):
  message: str
  device_id: str
  soh_pred_pct: float
  soh_pred: float
  rul_cycles: float
  rul_months: float
  rul_hours: float