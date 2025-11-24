'''
Recommendation Controller Module
This module defines the recommendation controller functions to handle recommendation logic.
'''

import os
import sys
from typing import List, Dict, Any, Literal

from src.exception.exception import CustomException
from src.logging.logging import logging
from src.service.impact_calculation import compute_ewaste_impact
from src.api.model.impact_model import (
  ImpactRequest,
  ImpactResponse,
  EwasteImpact
)

# Threshold constants
SOH_THRESHOLD_GOOD = 70.0
RUL_MONTHS_LONG = 24.0
RUL_MONTHS_SHORT = 3.0

# Define function to recommend action
def decide_recommendation_action(soh_pred_pct: float, rul_months: float, screen_label: str) -> Literal["hold_phone", "replace_screen", "replace_battery", "replace_phone"]:
  '''
  Function to recommend action based on state of health (SOH) and remaining useful life (RUL).\n
  params:
  - soh_pred_pct: Predicted State of Health percentage of the battery.
  - rul_months: Remaining Useful Life in months.
  - screen_label: Label indicating screen condition ("safe", "warning", "critical").
  returns:
  - Recommended action as a string literal.
  '''
  try:
    # Case for good battery health
    if soh_pred_pct >= SOH_THRESHOLD_GOOD and rul_months >= RUL_MONTHS_LONG:
      if screen_label == "safe":
        return "hold"
      else:
        return "replace_screen"
    
    # Case for moderate battery health
    if soh_pred_pct < SOH_THRESHOLD_GOOD and rul_months >= RUL_MONTHS_SHORT and screen_label == "safe":
      return "replace_battery"
    
    # Case for poor battery health or critical screen
    if soh_pred_pct < SOH_THRESHOLD_GOOD and rul_months < RUL_MONTHS_SHORT and screen_label in ["warning", "broken"]:
      return "replace_phone"
    
    # Fallback case
    if soh_pred_pct < SOH_THRESHOLD_GOOD:
      return "replace_battery"
    
    # Default action
    return "hold"
  except Exception as e:
    raise CustomException(e, sys)

# Define function for e-waste mitigation and calculation
def run_impact_calculation(payload: ImpactRequest) -> ImpactResponse:
  '''
  Function to calculate e-waste mitigation based on device parameters.\n
  params:
  - payload: ImpactRequest object containing device parameters.\n
  returns:
  - ImpactResponse object containing recommendation and impact metrics.
  '''
  try:
    logging.info(f"Running impact calculation for device_id: {payload.device_id}")
    
    # Decide recommendation action
    action = decide_recommendation_action(
      soh_pred_pct=payload.soh_pred_pct,
      rul_months=payload.rul_months,
      screen_label=payload.screen_label
    )
    logging.info(f"Recommended action: {action}")
    
    # Compute e-waste impact for both scenarios
    scenarios_result: Dict[str, EwasteImpact] = {}
    for scen in ["conservative", "optimistic"]:
      raw = compute_ewaste_impact(action=action, scenario=scen)
      scenarios_result[scen] = raw
    
    # Construct response model
    response = ImpactResponse(
      message="Impact calculation successful",
      device_id=payload.device_id,
      action=action,
      soh_pred_pct=payload.soh_pred_pct,
      rul_months=payload.rul_months,
      screen_label=payload.screen_label,
      scenarios=scenarios_result
    )
    logging.info(f"Impact calculation response: {response}")
    return response
  except Exception as e:
    raise CustomException(e, sys)