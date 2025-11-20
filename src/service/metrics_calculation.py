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
from src.core.soh_cycles import calculate_soh_cycles
from src.core.throughput_energy import (
  calculate_energy_consumption as core_calculate_energy_consumption, 
  calculate_throughput_energy_and_bot as core_calculate_throughput_energy_and_bot, 
  calculate_throughput as core_calculate_throughput
)

# Define metrics calculation class
class MetricsCalculation:
  def __init__(self, df: pd.DataFrame):
    self.df = df
  
  # Define function to internal base guard
  def _check_empty(self) -> bool:
    if self.df is None or self.df.empty:
      logging.info("Empty dataframe, nothing to compute.")
      return True
    return False
  
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
      if self._check_empty():
        return self.df
      logging.info("Calculating energy consumption...")
      output_df = core_calculate_energy_consumption(self.df)
      
      logging.info(
        output_df[["device_id", "created_at", "batt_voltage_v", "batt_current_a", "energy_wh"]].head()
      )
      return output_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def calculate_throughput_energy_and_bot(self) -> pd.DataFrame:
    '''
    Function to calculate throughput based energy consumption.\n
    params:
    - df: DataFrame containing raw data with battery and throughput metrics.
    \nreturns:
    - DataFrame with calculated throughput based energy consumption values.
    '''
    try:
      if self._check_empty():
        return self.df
      logging.info("Calculating throughput based energy consumption...")
      output_df = core_calculate_throughput_energy_and_bot(self.df)
      
      logging.info(
        output_df[["device_id", "created_at", "throughput_total_mbps", "energy_per_bit_avg_J", "BoT_mAh_per_Gbps",]].head()
      )
      return output_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def calculate_soh(self, roll_win: int = 3) -> pd.DataFrame:
    '''
    Function to calculate State of Health (SoH) from raw data.\n
    params:
    - df: DataFrame containing raw data with battery capacity metrics.
    \nreturns:
    - DataFrame with calculated SoH values.
    '''
    try:
      if self._check_empty():
        return self.df
      logging.info("Calculating State of Health (SoH)...")
      output_df = calculate_soh_cycles(self.df, roll_win=roll_win)
      
      # Rename columns
      rename_map = {}
      if "SoH_pct" in output_df.columns:
        rename_map["SoH_pct"] = "soh_pct"
      if "SoH_smooth" in output_df.columns:
        rename_map["SoH_smooth"] = "soh_smooth"
      if rename_map:
        output_df = output_df.rename(columns=rename_map)
      
      logging.info(
        output_df[[
          "device_id", "created_at", "Ct_mAh", "SoH", "soh_smooth", 
          "soh_pct" if "soh_pct" in output_df.columns else "SoH_pct", "soh_smooth" if "soh_smooth" in output_df.columns else "SoH_smooth_pct", "EFC"]].head()
      )
      return output_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def calculate_battery_cycles(self) -> pd.DataFrame:
    '''
    Function to calculate battery cycles from raw data.\n
    params:
    - df: DataFrame containing raw data with battery charge/discharge metrics.
    \nreturns:
    - DataFrame with calculated battery cycles values.
    '''
    try:
      if self._check_empty():
        return self.df
      logging.info("Calculating battery cycles...")
      output_df = calculate_soh_cycles(self.df)
      
      # Take frequently used columns
      cols = [
        c for c in ["device_id", "created_at", "Q_mAh", "delta_Q_mAh", "discharge_mAh", "EFC"] if c in output_df.columns
      ]
      out_subset = output_df[cols].copy()
      logging.info(out_subset.head())
      return out_subset
    except Exception as e:
      raise CustomException(e, sys)
  
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
      if self._check_empty():
        return self.df
      logging.info("Calculating throughput...")
      output_df = core_calculate_throughput(self.df)
      
      logging.info(
        output_df[["device_id", "created_at", "throughput_upload_mbps",
        "throughput_download_mbps", "throughput_total_mbps"]].head()
      )
      return output_df
    except Exception as e:
      raise CustomException(e, sys)