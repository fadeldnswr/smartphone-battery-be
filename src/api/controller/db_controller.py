'''
Database controller module for handling database operations.
'''

import os
import sys

from supabase import create_client, Client
from src.exception.exception import CustomException
from dotenv import load_dotenv
load_dotenv()

# Define function to create connection to supabase
def create_supabase_connection() -> Client:
  '''
  Function to create connection to Supabase database\n
  returns: 
    - Supabase client instance
  '''
  try:
    supabase: Client = create_client(
      os.getenv("SUPABASE_API_URL"),
      os.getenv("SUPABASE_API_KEY")
    )
    return supabase
  except Exception as e:
    raise CustomException(e, sys)