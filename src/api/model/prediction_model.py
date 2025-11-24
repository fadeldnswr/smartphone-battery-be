'''
Models for prediction visualization API responses.
'''
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Define soh series prediction model
class SoHPrediction(BaseModel):
  created_at: datetime
  soh_true: float
  soh_pred: float
  efc: float | None

# Define prediction response model
class PredictionResponse(BaseModel):
  message: str
  device_id: str
  soh_pred_pct: float
  soh_pred: float
  rul_cycles: float
  rul_months: float
  rul_hours: float
  soh_series: List[SoHPrediction]
  expiry_date: datetime
  mae_pct: float
  rmse_pct: float
  r2_soh: float

# Define image prediction model
class ImagePredictionResponse(BaseModel):
  message: str = Field("Image prediction successful", description="Response message indicating the status of the image prediction.")
  class_label: str = Field(..., description="Predicted class label for the input image.")
  ui_bucket: str = Field(..., description="UI bucket corresponding to the predicted class label.")
  score: float = Field(..., description="Confidence score of the prediction.")
  probabilities: Dict[str, float] = Field(..., description="Dictionary of probabilities for each class label.")
  rep_score: float = Field(..., description="Representative score associated with the predicted class label.")
  severity_weight: float = Field(..., description="Severity weight associated with the predicted class label.")
  config_version: str = Field(None, description="Version of the model configuration used for prediction.")
  model_type: str = Field(None, description="Type of the model used for prediction.")