'''
Data ingestion module for handling data operations with Supabase database.
'''

import sys
import pandas as pd

from src.api.controller.db_controller import create_supabase_connection
from src.exception.exception import CustomException
from src.logging.logging import logging
from src.api.model.raw_metrics import RawMetrics

# Define data ingestion class
class DataIngestion:
  def __init__(self, table_name:str, device_id:str | None = None):
    self.table_name = table_name
    self.device_id = device_id
    self.supabase = create_supabase_connection()
  
  def extract_data_from_db(self, limit: int = 200) -> pd.DataFrame:
    '''
    Function to extract data from Supabase database table.
    \nparams:
    - table_name: Name of the table to extract data from.
    - deivice_id: Device ID to filter the data.
    \nreturns:
    - DataFrame containing the extracted data.
    '''
    try:
      # Fetch data from specified table
      logging.info(f"Extracting data from table: {self.table_name}...")
      response = (
        self.supabase.table(self.table_name)
        .select("*")
        .order("ts_utc", desc=True))
      
      # Check for device_id filter
      if self.device_id:
        response = response.eq("device_id", self.device_id)
      response = response.limit(limit).execute()
      
      result = response.data
      logging.info("Data extraction completed successfully.")
      return pd.DataFrame(result)
    except Exception as e:
      raise CustomException(e, sys)