'''
Database controller module for handling database operations.
'''

import os
import sys

from supabase import create_client, Client
from src.logging.logging import logging
from src.exception.exception import CustomException

# Define function to create connection to supabase
def create_supabase_connection() -> Client:
  '''
  Function to create connection to Supabase database\n
  returns: 
    - Supabase client instance
  '''
  try:
    supabase: Client = create_client(
      os.getenv("SUPABASE_URL"),
      os.getenv("SUPABASE_API_KEY")
    )
    return supabase
  except Exception as e:
    raise CustomException(e, sys)

# Define function to fetch data from database
def get_data_from_db():
  '''
  Function to fetch data from Supabase database\n
  returns: 
  - List of records from the database
  '''
  try:
    # Initialize supabase connection
    logging.info("Fetching data from database...")
    supabase = create_supabase_connection()
    
    # Fetch data from supabase table
    response = supabase.table("raw_smartphone_data").select("*").execute()
    data = response.data
    logging.info("Data fetched successfully.")
    return data
  except Exception as e:
    raise CustomException(e, sys)

# Define function to insert data into database
def insert_data_to_db(data):
  '''
  Function to insert data into Supabase database\n
  parameters:
  - data (list of dicts): Data to be inserted
  \nreturns: 
  - Response from the insert operation
  '''
  try:
    # Initialize supabase connection
    logging.info("Inserting data into database...")
    supabase = create_supabase_connection()
    
    # Insert data into supabase table
    response = supabase.table("raw_smartphone_data").insert(data).execute()
    logging.info("Data inserted successfully.")
    return response
  except Exception as e:
    raise CustomException(e, sys)