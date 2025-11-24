'''
Module for calculating the expiry date of a smartphone battery based on its remaining useful life (RUL) in months.
'''
from datetime import datetime, timedelta
from src.exception.exception import CustomException

import os
import sys

def compute_expiry_date(rul_months: float) -> datetime:
  '''
  Function to compute the expiry date of a smartphone battery based on its remaining useful life (RUL) in months.
  params:
  - rul_months: Remaining Useful Life in months.
  returns:
  - Expiry date as a datetime object.
  '''
  try:
    # Check if RUL exists
    if rul_months is None:
      return datetime.now()
    
    # Calculate expiry date
    months = max(float(rul_months), 0)
    expiry_date = datetime.now() + timedelta(days=months * 30)
    return expiry_date
  except Exception as e:
    raise CustomException(e, sys)