'''
Data load for handling data operations with Supabase database.
'''

import os 
import sys

from src.exception.exception import CustomException
from src.logging.logging import logging
from src.api.controller.db_controller import create_supabase_connection

# Define data load class
class DataLoad:
  def __init__(self):
    pass
  
  def load_data_to_db(self):
    pass