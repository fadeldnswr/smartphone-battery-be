'''
Data load for handling data operations with Supabase database.
'''

import os 
import sys
import pandas as pd

from src.exception.exception import CustomException
from src.logging.logging import logging
from src.api.controller.db_controller import create_supabase_connection
from src.pipeline.data_transformation import DataTransformation

# Define data load class
class DataLoad:
  def __init__(self, target_table:str):
    self.supabase = create_supabase_connection()
    self.target_table = target_table
  
  def load_data_to_db(self, df: pd.DataFrame) -> pd.DataFrame | None:
    '''
    Function to load data to Supabase database table.
    \nparams:
    - df: DataFrame containing the data to be loaded.
    \nreturns:
    - DataFrame containing the loaded data or None if failed.
    '''
    try:
      # Check if dataframe is empty
      if df.empty:
        logging.info("DataFrame is empty. No data to load.")
        return df
      
      # Load data to specified table
      logging.info(f"Loading data to table: {self.target_table}...")
      records = df.to_dict(orient="records")
      self.supabase.table(self.target_table).upsert(records).execute()
    except Exception as e:
      raise CustomException(e, sys)