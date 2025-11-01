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
  def __init__(self, table_name:str, response:RawMetrics):
    self.table_name = table_name
    self.supabase = None
    self.device_id = None
    self.response = response
  
  def extract_data_from_db(self) -> pd.DataFrame:
    '''
    Function to extract data from Supabase database table.
    \nparams:
    - table_name: Name of the table to extract data from.
    - deivice_id: Device ID to filter the data.
    \nreturns:
    - DataFrame containing the extracted data.
    '''
    try:
      # Create supabase connection
      logging.info("Creating Supabase connection...")
      self.supabase = create_supabase_connection()
      
      # Fetch data from specified table
      logging.info(f"Extracting data from table: {self.table_name}...")
      response = (
        self.supabase.table(self.table_name)
        .select("*")
        .filter("device_id")
        .eq(self.device_id)
        .execute()
      )
      
      # Check if response data equal to RawMetrics model
      if response.data != RawMetrics:
        logging.error("Response data does not match RawMetrics model!")
        raise CustomException("Response data does not match RawMetrics model!", sys)
      else:
        # Convert data to dataframe
        logging.info("Converting data to DataFrame...")
        df = pd.DataFrame(
          response.data, 
          columns=response.data[0].keys() if response.data else []
          )
        
        # Return the dataframe
        return df
    except Exception as e:
      raise CustomException(e, sys)