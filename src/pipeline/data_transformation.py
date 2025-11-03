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
      throughput_data = MetricsCalculation(df=self.data)
      throughput_df = throughput_data.calculate_throughput()
      
      logging.info("Troughput calculation completed successfully.")
      return throughput_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def compute_energy(self) -> pd.DataFrame:
    '''
    Function to compute energy consumption from raw data.
    '''
    try:
      # Perform energy computation
      logging.info("Computing energy consumption...")
      energy_data = MetricsCalculation(df=self.data)
      energy_df = energy_data.calculate_energy_consumption()
      
      logging.info("Energy consumption calculation completed successfully.")
      return energy_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def compute_metrics(self) -> pd.DataFrame:
    '''
    Function to compute both throughput and energy consumption metrics.
    '''
    try:
      calc = MetricsCalculation(df=self.data)
      
      # Compute throughput metrics
      logging.info("Computing throughput metrics...")
      throughput_df = calc.calculate_throughput()
      
      # Compute energy consumption metrics
      logging.info("Computing energy consumption metrics...")
      energy_df = calc.calculate_energy_consumption()
      
      # Check if dataframes are empty
      if throughput_df is None or throughput_df.empty:
        return energy_df
      if energy_df is None or energy_df.empty:
        return throughput_df
      
      # Merge dataframes on common columns
      logging.info("Merging throughput and energy data...")
      merged_df = pd.merge(throughput_df, energy_df[["device_id", "created_at", "energy_wh"]], on=["device_id", "created_at"], how="left")
      
      logging.info("Metrics computation completed successfully.")
      return merged_df
    except Exception as e:
      raise CustomException(e, sys)