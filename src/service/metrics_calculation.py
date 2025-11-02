'''
Metrics calculation module to compute derived metrics from raw data such as Energy Consumption,
Throughput Based Energy Consumption, SoH, RUL, and other relevant performance indicators.
'''

import os
import sys
import numpy as np
import pandas as pd

from src.exception.exception import CustomException
from src.logging.logging import logging

# Define metrics calculation class
class MetricsCalculation:
  def __init__(self, df: pd.DataFrame):
    self.df = df
  
  def calculate_energy_consumption(self):
    '''
    Function to calculate energy consumption from raw data.
    '''
    pass
  
  def calculate_throughput_based_energy_consumption(self):
    '''
    Function to calculate throughput based energy consumption.
    '''
    pass
  
  def calculate_soh(self):
    '''
    Function to calculate State of Health (SoH) from raw data.
    '''
    pass
  
  def calculate_battery_cycles(self):
    '''
    Function to calculate battery cycles from raw data.
    '''
    pass
  
  def calculate_rul(self):
    '''
    Function to calculate Remaining Useful Life (RUL) from raw data.
    '''
    pass
  
  def calculate_throughput(self) -> pd.DataFrame:
    '''
    Function to calculate throughput from raw data.
    '''
    try:
      # Check if dataframe is not empty
      if self.df.empty:
        return self.df
      
      # Copy the dataframe and sort by device_id and created_at
      new_df = self.df.copy()
      new_df["created_at"] = pd.to_datetime(new_df["created_at"])
      new_df = new_df.sort_values(["device_id", "created_at"])
      
      new_df = new_df.dropna(subset=["tx_total_bytes", "rx_total_bytes"])
      
      # Calculate delta per device
      logging.info("Computing deltas for throughput calculation...")
      new_df["delta_t"] = new_df.groupby("device_id")["created_at"].diff().dt.total_seconds()
      new_df["delta_tx_bytes"] = new_df.groupby("device_id")["tx_total_bytes"].diff()
      new_df["delta_rx_bytes"] = new_df.groupby("device_id")["rx_total_bytes"].diff()
      
      # Handle first entries and negative deltas
      logging.info("Filtering invalid delta entries...")
      new_df = new_df.dropna(subset=["delta_t", "delta_tx_bytes", "delta_rx_bytes"])
      
      # Calculate throughput Mbps
      logging.info("Calculating throughput values...")
      new_df["throughput_upload_bps"] = (new_df["delta_tx_bytes"] * 8) / new_df["delta_t"]
      new_df["throughput_download_bps"] = (new_df["delta_rx_bytes"] * 8) / new_df["delta_t"]
      new_df["throughput_total_bps"] = ((new_df["delta_tx_bytes"] + new_df["delta_rx_bytes"]) * 8) / new_df["delta_t"]

      # Mbps (lebih enak ditampilkan)
      new_df["throughput_upload_mbps"] = new_df["throughput_upload_bps"] / 1e6
      new_df["throughput_download_mbps"] = new_df["throughput_download_bps"] / 1e6
      new_df["throughput_total_mbps"] = new_df["throughput_total_bps"] / 1e6
      
      logging.info(new_df[["created_at", "throughput_upload_mbps", "throughput_download_mbps", "throughput_total_mbps"]].head())
      
      return new_df
    except Exception as e:
      raise CustomException(e, sys)