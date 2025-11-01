'''
Data Transformation Module
This module handles data transformation operations for the pipeline.
'''

import pandas as pd
import os
import sys

from src.logging.logging import logging
from src.exception.exception import CustomException
from src.pipeline.data_ingestion import DataIngestion

# Define data transformation class
class DataTransformation:
  def __init__(self, data: pd.DataFrame):
    self.data = None
  
  def transform_data(self) -> pd.DataFrame:
    '''
    Function to transform raw data into a suitable format for analysis.
    '''
    try:
      # Initiate data ingestion
      logging.info("Starting data ingestion...")
      self.data = DataIngestion(table_name="raw_metrics")
      self.data.extract_data_from_db()
      
      # Perform data transformation equation
      logging.info("Transforming data...")
    except Exception as e:
      raise CustomException(e, sys)