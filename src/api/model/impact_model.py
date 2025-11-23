'''
Model definitions for impact analysis.
This module defines data models used for representing the impact analysis results.
'''

from pydantic import BaseModel
from typing import List, Dict, Any

class EwasteImpact(BaseModel):
  scenario: str
  n_devices: int
  n_A: int
  n_B: int
  n_C: int
  n_D: int
  n_eligible: int
  phones_saved: float
  ewaste_baseline_kg: float
  ewaste_pred_kg: float
  ewaste_reduced_kg: float
  co2_reduced_kg: float
  r: float
  alpha: float
  mass_per_phone_kg: float
  co2_per_phone_kg: float