'''
Application usage calculation module.
This module contains functions to calculate application usage statistics
'''

import pandas as pd
import numpy as np
import os
import sys

from typing import Dict, Any
from src.logging.logging import logging
from src.exception.exception import CustomException
from src.service.metrics_calculation import MetricsCalculation

# Define class for usage calculation
class UsageCalculation:
  def __init__(self, df: pd.DataFrame):
    self.df = df
  
  def _base_guard(self, df: pd.DataFrame) -> pd.DataFrame:
    '''
    Function to perform base checks on the input DataFrame.\n
    returns:
    - pd.DataFrame : Validated DataFrame
    '''
    try:
      # Check if df is empty
      if df is None or df.empty:
        logging.info("Input DataFrame is empty.")
        return df
      
      # Copy dataframe to avoid modifying original
      df = df.copy()
      
      # Ensure created_at columns is in datetime format
      df["created_at"] = pd.to_datetime(df["created_at"])
      
      # Sort dataframe by device_id and created_at
      df = df.sort_values(["device_id", "created_at"])
      return df
    except Exception as e:
      raise CustomException(e, sys)
  
  def calculate_app_usage(self, top_rank: int = 4) -> pd.DataFrame:
    '''
    Calculate application usage statistics from raw data.\n
    params:
    - df : pd.DataFrame : DataFrame containing raw application usage data\n
    returns:
    - pd.DataFrame : DataFrame containing calculated application usage statistics
    '''
    try:
      # Create base guard
      df = self._base_guard(self.df)
      if df.empty or df is None:
        return df

      # Ensure fg_pkg cols exist
      if "fg_pkg" not in df.columns:
        logging.info("fg_pkg column not found in DataFrame.")
        return pd.DataFrame()
      
      # Calculatae total throughput (Mbps)
      thr_df = MetricsCalculation(df).calculate_throughput()
      if thr_df.empty:
        logging.info("Throughput calculation resulted in empty DataFrame.")
        return pd.DataFrame()
      
      # Clean app data
      thr_df = thr_df.copy()
      thr_df = thr_df.dropna(subset=["fg_pkg"])
      
      # Prepare delta bytes and duration
      thr_df["delta_t"] = thr_df["delta_t"].clip(lower=0).fillna(0)
      thr_df["delta_tx_bytes"] = thr_df["delta_tx_bytes"].clip(lower=0).fillna(0)
      thr_df["delta_rx_bytes"] = thr_df["delta_rx_bytes"].clip(lower=0).fillna(0)
      thr_df["delta_total_bytes"] = thr_df["delta_tx_bytes"] + thr_df["delta_rx_bytes"]
      
      # Group by device + app
      grouped_df = (
        thr_df
        .groupby(["device_id", "fg_pkg"], as_index=False)
        .agg(
          total_bytes=("delta_total_bytes", "sum"),
          total_duration_s=("delta_t", "sum")
        )
      )
      
      # Derived metrics
      grouped_df["total_mb"] = grouped_df["total_bytes"] / 1e6
      grouped_df["avg_throughput_mbps"] = np.where(
        grouped_df["total_duration_s"] > 0,
        (grouped_df["total_bytes"] * 8 / grouped_df["total_duration_s"]) / 1e6, 0.0,
      )
      
      # Rank per device
      grouped_df["rank"] = (
        grouped_df
        .groupby("device_id")["total_mb"]
        .rank(method="first", ascending=False)
      )
      
      # Sort and filter top apps
      top_apps = (
        grouped_df[grouped_df["rank"] <= top_rank]
        .sort_values(by=["device_id", "rank"])
        .reset_index(drop=True)
      )
      
      logging.info("Top application usage statistics calculated successfully.")
      logging.info(top_apps[["device_id", "fg_pkg", "total_mb", "avg_throughput_mbps", "rank"]])
      return top_apps
    except Exception as e:
      raise CustomException(e, sys)