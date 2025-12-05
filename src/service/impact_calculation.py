'''
Class for impact calculation service.
This module provides functionalities to calculate the environmental impact
of various operations based on input data.
'''

from dataclasses import dataclass
from typing import List, Dict, Any

from src.logging.logging import logging
from src.exception.exception import CustomException
from src.api.model.impact_model import EwasteImpact
from src.service.carbon_equivalent_calculation import carbon_to_car_km

import pandas as pd
import os
import sys

# Define constants for impact factors
MASS_PHONE_KG = 0.18 # Average mass of a smartphone in kg
MASS_PHONE_BATTERY_KG = 0.04 # Average mass of a smartphone battery in kg
MASS_PHONE_SCREEN_KG = 0.05 # Average mass of a smartphone screen in kg
CARBON_PER_KG = 60 # Emission factor for smartphone production in kg CO2

# Define e-waste mitigation scenarios
SCENARIOS = {
  "conservative": {"r": 0.3, "alpha": 0.3},
  "optimistic": {"r": 0.5, "alpha": 0.7},
}

# Create function to compute ewaste impact
def compute_ewaste_impact(
  action: str, 
  scenario: str = "conservative",
  phone_mass_kg: float = MASS_PHONE_KG) -> EwasteImpact:
  '''
  Function to compute e-waste impact based on summary data and scenario.\n
  params:
  - df_summary: DataFrame containing summary statistics for devices.\n
  - scenario: Scenario type for impact calculation (default: "conservative").\n
  returns:
  - EwasteImpact object containing calculated impact metrics.
  '''
  try:
    # Check if scenario is valid
    if scenario not in SCENARIOS:
      raise ValueError(f"Invalid scenario: {scenario}. Choose from {list(SCENARIOS.keys())}")
    
    # Define alpha and r based on scenario
    alpha = SCENARIOS[scenario]["alpha"]
    
    # Case for reuse action
    if action == "replace_phone":
      ewaste_baseline = phone_mass_kg
      ewaste_with_system = phone_mass_kg
    if action == "replace_battery":
      # Case for battery replacement
      ewaste_baseline = phone_mass_kg
      ewaste_with_system = MASS_PHONE_BATTERY_KG
      ewaste_reduced = ewaste_baseline - ewaste_with_system
      carbon_saved = ewaste_reduced * CARBON_PER_KG
      car_km = carbon_to_car_km(carbon_saved_kg=carbon_saved)
      # Return EwasteImpact object
      return EwasteImpact(
        alpha=alpha,
        ewaste_baseline_kg=ewaste_baseline,
        ewaste_with_system_kg=ewaste_with_system,
        ewaste_reduced_kg=ewaste_reduced,
        carbon_saved_kg=carbon_saved,
        car_km_equivalent=car_km
      )
    if action == "replace_screen":
      ewaste_baseline = phone_mass_kg
      ewaste_with_system = MASS_PHONE_SCREEN_KG
    else:
      ewaste_baseline = phone_mass_kg
      ewaste_with_system = (1 - alpha) * phone_mass_kg
    
    # Case for hold/ screen repair / battery repair
    ewaste_reduced = ewaste_baseline - ewaste_with_system
    carbon_saved = ewaste_reduced * CARBON_PER_KG
    car_km = carbon_to_car_km(carbon_saved_kg=carbon_saved)
    
    # Return EwasteImpact object
    return EwasteImpact(
      alpha=alpha,
      ewaste_baseline_kg=ewaste_baseline,
      ewaste_with_system_kg=ewaste_with_system,
      ewaste_reduced_kg=ewaste_reduced,
      carbon_saved_kg=carbon_saved,
      car_km_equivalent=car_km
    )
  except Exception as e:
    logging.error("Error in compute_ewaste_impact", e)
    raise CustomException(e, sys)