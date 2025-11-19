'''
Data Transformation Module
This module handles data transformation operations for the pipeline.
'''

import pandas as pd
import os
import sys
import numpy as np

from src.logging.logging import logging
from src.exception.exception import CustomException
from src.service.metrics_calculation import MetricsCalculation
from src.service.usage_calculation import UsageCalculation

# Define data transformation class
class DataTransformation:
  def __init__(self, data: pd.DataFrame):
    self.data = data
  
  def compute_throughput(self) -> pd.DataFrame:
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
  
  def compute_throughput_and_bot(self) -> pd.DataFrame:
    '''
    Function to compute throughput based energy consumption and battery cost of traffic.
    '''
    try:
      # Perform throughput based energy computation
      logging.info("Computing throughput based energy consumption and battery cost of traffic...")
      bot_data = MetricsCalculation(df=self.data)
      bot_df = bot_data.calculate_throughput_energy_and_bot()
      
      logging.info("Throughput based energy consumption and battery cost of traffic calculation completed successfully.")
      return bot_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def compute_cycles(self) -> pd.DataFrame:
    '''
    Function to compute battery cycles from raw data.
    '''
    try:
      # Perform battery cycles computation
      logging.info("Computing battery cycles...")
      cycles_data = MetricsCalculation(df=self.data)
      cycles_df = cycles_data.calculate_battery_cycles()
      
      logging.info("Battery cycles calculation completed successfully.")
      return cycles_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def compute_soh(self) -> pd.DataFrame:
    '''
    Function to computer State of Health (SoH) from raw data.
    '''
    try:
      # Perform SoH computation
      logging.info("Computing State of Health (SoH)...")
      soh_data = MetricsCalculation(df=self.data)
      soh_df = soh_data.calculate_soh()
      
      logging.info("State of Health (SoH) calculation completed successfully.")
      return soh_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def compute_usage_application(self, top_rank: int = 4) -> pd.DataFrame:
    '''
    Function to compute application usage statistics.\n
    params:
    - top_rank : int : Number of top applications to consider for usage statistics\n
    returns:
    - pd.DataFrame : DataFrame containing application usage statistics
    '''
    try:
      logging.info("Computing application usage statistics...")
      usage_data = UsageCalculation(df=self.data)
      usage_df = usage_data.calculate_app_usage(top_rank=top_rank)
      
      logging.info("Application usage statistics calculation completed successfully.")
      return usage_df
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
      
      # Compute energy per bit and battery cost of traffic metrics
      logging.info("Calculate energy per bit and battery cost of traffic metrics...")
      energy_bot_df = calc.calculate_throughput_energy_and_bot()
      
      # Compute battery cycles metrics
      logging.info("Calculate battery cycles metrics...")
      cycles_df = calc.calculate_battery_cycles()
      
      # Compute State of Health (SoH) metrics
      logging.info("Calculate State of Health (SoH) metrics...")
      soh_df = calc.calculate_soh()
      
      # Check if dataframes are empty
      if (throughput_df is None or throughput_df.empty) and (energy_df is None or energy_df.empty):
        return pd.DataFrame()
      
      # Merge dataframes on common columns
      logging.info("Merging throughput and energy data...")
      merged_df = pd.merge(
        throughput_df, 
        energy_df[["device_id", "created_at", "energy_wh", "batt_voltage_v"]], 
        on=["device_id", "created_at"], how="left"
      )
      
      # Check if energy_bot_df is not empty before merging
      if energy_bot_df is not None and not energy_bot_df.empty:
        merged_df = pd.merge(
          merged_df,
          energy_bot_df[["device_id", "created_at", "energy_per_bit_tx_J", "energy_per_bit_rx_J", "energy_per_bit_avg_J", "BoT_mAh_per_Gbps"]],
          on=["device_id", "created_at"], how="left"
        )
      
      # Check if cycles_df is not empty before merging
      if cycles_df is not None and not cycles_df.empty:
        merged_df = pd.merge(
          merged_df,
          cycles_df[["device_id", "created_at", "charge_counter_uah", "delta_charge_uah", "discharge_uah", "cycles_est"]],
          on=["device_id", "created_at"], how="left"
        )
      
      # Check if soh_df is not empty before merging
      if soh_df is not None and not soh_df.empty:
        merged_df = pd.merge(
          merged_df,
          soh_df[["device_id", "created_at", "Q_mAh", "Ct_mAh", "soh_pct", "soh_smooth"]],
          on=["device_id", "created_at"], how="left"
        )
      
      logging.info("Metrics computation completed successfully.")
      return merged_df
    except Exception as e:
      raise CustomException(e, sys)
  
  def compute_monitoring_summary(self, window_hours: int = 1) -> pd.DataFrame:
    '''
    Function to compute monitoring summary over a specified time window.\n
    params:
    - window_hours : int : Time window in hours for summary computation\n
    returns:
    - pd.DataFrame : DataFrame containing monitoring summary
    '''
    try:
      logging.info("Computing monitoring summary...")
      metrics_df = self.compute_metrics()
      
      # Check if metrics_df is empty
      if metrics_df is None or metrics_df.empty:
        return pd.DataFrame()
      
      # Copy metrics_df to summary_df
      df = metrics_df.copy()
      
      # Check if created_at column exists
      if "created_at" not in df.columns:
        logging.error("created_at column is missing in the data.")
        return pd.DataFrame()
      df["created_at"] = pd.to_datetime(df["created_at"]) # Ensure created_at is in datetime format
      df = df.sort_values(by="created_at") # Sort by created_at
      
      # Create list of summary metrics
      summary: list = []
      for dev, g in df.groupby("device_id"):
        if g.empty:
          continue
        g = g.sort_values(by="created_at")
        last_time = g["created_at"].max()
        
        # Create window for summary calculation
        window_start = last_time - pd.Timedelta(hours=window_hours)
        window_data = g[(g["created_at"] > window_start) & (g["created_at"] <= last_time)]
        if window_data.empty:
          continue
        
        # Today summary
        day_start = last_time.normalize()
        today_mask = (g["created_at"] >= day_start) & (g["created_at"] <= last_time)
        today = g.loc[today_mask]
        
        # Append summary metrics to list
        summary.append({
          "device_id": dev,
          "window_start": window_start,
          "window_end": last_time,
          "sample_last": len(window_data),
          
          # Last 1 hour metrics
          "energy_last_wh": window_data["energy_wh"].sum(skipna=True) 
          if "energy_wh" in window_data.columns else np.nan,
          "avg_thr_last_mbps": window_data["throughput_total_mbps"].mean(skipna=True) 
          if "throughput_total_mbps" in window_data.columns else np.nan,
          "avg_bot_last": window_data["BoT_mAh_per_Gbps"].mean(skipna=True)
          if "BoT_mAh_per_Gbps" in window_data.columns else np.nan,
          "avg_epb_last": window_data["energy_per_bit_avg_J"].mean(skipna=True)
          if "energy_per_bit_avg_J" in window_data.columns else np.nan,
          
          # Total energy today
          "energy_today_wh": today["energy_wh"].sum(skipna=True)
          if (not today.empty and "energy_wh" in today.columns) else np.nan,
        })
      summary_df = pd.DataFrame(summary)
      logging.info("Monitoring summary computation completed successfully.")
      logging.info(f"Summary DataFrame shape: {summary_df.shape}")
      return summary_df
    except Exception as e:
      raise CustomException(e, sys)