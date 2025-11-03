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
    self.alpha_tx = 446.
    self.beta_tx = 3.381132
    self.alpha_rx = 357.5443
    self.beta_rx = 1.969068
  
  def _base_guard(self, df:pd.DataFrame) -> pd.DataFrame:
    '''
    Function to perform base checks on dataframe.\n
    params:
    - df: DataFrame to be checked.
    \nreturns:
    - DataFrame after checks.
    '''
    # Check if dataframe is None or empty
    if df is None or df.empty:
      logging.info("Empty dataframe, nothing to compute.")
      return df
    
    # Ensure created_at is datetime and sort values
    df = df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values(["device_id", "created_at"])
    return df
  
  def calculate_energy_consumption(self) -> pd.DataFrame:
    '''
    Function to calculate energy consumption from raw data.\n
    params:
    - df: DataFrame containing raw data with battery voltage and current metrics.
    \nreturns:
    - DataFrame with calculated energy consumption values.
    '''
    try:
      # Create a copy of dataframe
      new_df = self._base_guard(self.df)
      
      # Check if dataframe is not empty
      if new_df.empty or new_df is None:
        return new_df
      
      # Make sure created_at is datetime
      logging.info("Calculating energy consumption...")
      new_df = self.df.copy()
      new_df["created_at"] = pd.to_datetime(new_df["created_at"])
      new_df = new_df.sort_values(["device_id", "created_at"])
      
      # Calculate delta per device
      new_df["delta_t"] = new_df.groupby("device_id")["created_at"].diff().dt.total_seconds()
      
      # Convert to volt and ampere
      logging.info("Converting battery metrics to standard units...")
      new_df["batt_voltage_v"] = new_df["batt_voltage_mv"] / 1000
      new_df["batt_current_a"] = new_df["current_avg_ua"] / 1000000
      
      # Calculate energy per step
      logging.info("Computing energy consumption values...")
      new_df["energy_wh"] = (new_df["batt_voltage_v"] * new_df["batt_current_a"] * new_df["delta_t"]) / 3600
      
      # Return dataframe with energy consumption
      logging.info(new_df[["created_at", "batt_voltage_v", "batt_current_a", "energy_wh"]].head())
      return new_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def calculate_throughput_energy_and_bot(self) -> pd.DataFrame:
    '''
    Function to calculate throughput based energy consumption.
    '''
    try:
      # Create a copy of dataframe
      new_df = self._base_guard(self.df)
      
      # Check if dataframe is not empty
      if new_df.empty or new_df is None:
        return new_df
      
      # Calculate throughput first
      thr_calc = self.calculate_throughput()
      energy_calc = self.calculate_energy_consumption()
      
      # Merge both dataframes on device_id and created_at
      df = pd.merge(
        thr_calc[["device_id", "created_at", "throughput_total_bps"]],
        energy_calc[["device_id", "created_at", "batt_voltage_v", "energy_wh"]],
        on=["device_id", "created_at"],
        how="inner",
      ).sort_values(["device_id", "created_at"])
      
      # Make sure throughput data dont have zero values
      df["throughput_total_bps"] = df["throughput_total_bps"].replace(0, np.nan)
      
      # Calculate energy per bit
      df["energy_per_bit_tx"] = (self.alpha_tx / df["throughput_total_bps"]) + self.beta_tx
      df["energy_per_bit_rx"] = (self.alpha_rx / df["throughput_total_bps"]) + self.beta_rx
      df["energy_per_bit_tx_J"] = df["energy_per_bit_tx"] * 1e-9
      df["energy_per_bit_rx_J"] = df["energy_per_bit_rx"] * 1e-9
      
      # Total combination of energy per bit
      df["energy_per_bit_avg_J"] = (df["energy_per_bit_tx_J"] + df["energy_per_bit_rx_J"]) / 2
      
      # Convert to volt and ampere for battery cost of traffic calculation
      V_avg = df["batt_voltage_v"].mean()
      
      # Calculate Battery cost of traffic (BoT) in mAh per Gbps
      df["BoT_mAh_per_Gbps"] = (df["energy_per_bit_avg_J"] * (8 * 1e9) / V_avg) * (1000 / 3600)
      
      # Return dataframe with throughput based energy consumption
      return df

    except Exception as e:
      raise CustomException(e, sys)
  
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
    Function to calculate throughput from raw data.\n
    params:
    - df: DataFrame containing raw data with tx_total_bytes and rx_total_bytes metrics.
    \nreturns:
    - DataFrame with calculated throughput values.
    '''
    try:
      # Create a copy of dataframe
      new_df = self._base_guard(self.df)
      
      # Check if dataframe is not empty
      if new_df.empty or new_df is None:
        return new_df
      
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