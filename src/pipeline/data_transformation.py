'''
Data Transformation Module
This module handles data transformation operations for the pipeline.
'''

import pandas as pd
import os
import sys

from src.logging.logging import logging
from src.exception.exception import CustomException
from src.service.metrics_calculation import MetricsCalculation

# Define data transformation class
class DataTransformation:
  def __init__(self, data: pd.DataFrame):
    self.data = data
  
  def compute_metrics(self) -> pd.DataFrame:
    '''
    Function to transform raw data into a suitable format for analysis.
    '''
    try:
      # Perform data transformation equation
      logging.info("Transforming data...")
      transformed_data = MetricsCalculation(df=self.data)
      transformed_data.calculate_throughput()
      transformed_data.calculate_energy_consumption()
      
      logging.info("Troughput calculation completed successfully.")
      return transformed_data
    except Exception as e:
      raise CustomException(e, sys)