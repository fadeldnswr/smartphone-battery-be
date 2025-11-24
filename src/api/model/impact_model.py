'''
Model definitions for impact analysis.
This module defines data models used for representing the impact analysis results.
'''

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

# Define e-waste impact model
class EwasteImpact(BaseModel):
  alpha: float = Field(..., description="Proportion of e-waste mitigated through the system")
  ewaste_baseline_kg: float
  ewaste_with_system_kg: float
  ewaste_reduced_kg: float
  carbon_saved_kg: float

# Define impact request model
class ImpactRequest(BaseModel):
  device_id: str
  soh_pred_pct: float = Field(..., description="Predicted State of Health percentage of the battery")
  rul_months: float = Field(..., description="Remaining Useful Life in months")
  screen_label: Literal["safe", "warning", "broken"]

# Define impact response model
class ImpactResponse(BaseModel):
  message: str
  device_id: str
  action: Literal["hold", "replace_phone", "replace_battery", "replace_screen"]
  soh_pred_pct: float
  rul_months: float
  screen_label: Literal["safe", "warning", "broken"]
  scenarios: Dict[Literal["conservative", "optimistic"], EwasteImpact]