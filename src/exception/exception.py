'''
Exception handling module for the application.
This module defines custom exceptions used throughout the application.
It includes exceptions for invalid configurations, data processing errors,
and simulation errors.
'''

import sys
from src.logging.logging import logging

# Create custom exceptions for the application
class CustomException(Exception):
  '''Base class for all custom exceptions in the application.'''
  def __init__(self, message, error_details: sys):
    super().__init__(message)
    self.message = message
    _,_,exc_tb = error_details.exc_info()
    
    self.line_no = exc_tb.tb_lineno
    self.file_name = exc_tb.tb_frame.f_code.co_filename
  
  def __str__(self):
    return "Error occured in python script name [{0}] line number [{1}] error message : [{2}]".format(
      self.file_name, self.line_no, str(self.message)
    )