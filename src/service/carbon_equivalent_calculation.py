'''
Docstring for service.carbon_equivalent_calculation
'''
import os
import sys

from src.exception.exception import CustomException
from src.logging.logging import logging

# Define function to compute carbon equivalent
CAR_EMISSION_KG_PER_KM = 0.192  # Average car emissions in kg CO2 per km
def carbon_to_car_km(carbon_saved_kg: float) -> float:
  '''
  Docstring for carbon_to_car_km
  
  :param carbon_saved_kg: Description
  :type carbon_saved_kg: float
  :return: Description
  :rtype: float
  '''
  try:
    # Check for valid input
    if carbon_saved_kg is None:
      return 0.0
    
    # Calculate equivalent car kilometers
    km = carbon_saved_kg / CAR_EMISSION_KG_PER_KM
    return max(km, 0.0)
  except Exception as e:
    raise CustomException(e, sys)