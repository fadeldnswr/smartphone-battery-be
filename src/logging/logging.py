'''
This module provides a simple logging utility that can be used to log messages to the console.
It includes functions to log messages at different levels (info, warning, error) and can be extended to log to files or other outputs.
''' 

import logging
import os
import sys
from datetime import datetime

# Define the log file name with the current date and time
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

# Define logging path
log_path = os.path.join(os.getcwd(), "logs", LOG_FILE)
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# Define the full path for the log file
LOG_FILE_PATH = log_path

# Configure logging to write to the log file
logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)