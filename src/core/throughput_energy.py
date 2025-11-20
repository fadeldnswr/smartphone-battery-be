'''
Module for throughput energy calculations for smartphone batteries.
This module includes functions to compute throughput and energy metrics
based on battery usage data.
'''

import numpy as np
import pandas as pd

from .config import TIMESTAMP_COL, DEVICE_COL

# Define constants
ALPHA_TX = 446.0
BETA_TX = 3.381132
ALPHA_RX = 357.5443
BETA_RX = 1.969068

# Define base guard function
def base_guard(df: pd.DataFrame) -> pd.DataFrame:
  '''
  Function to apply basic data validation and sorting on the input dataframe.\n
  params:
  - df: Input dataframe with battery usage data.\n
  returns:
  - Validated and sorted dataframe.
  '''
  try:
    if df is None or df.empty:
      return df
    df = df.copy()
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL])
    df = df.sort_values([DEVICE_COL, TIMESTAMP_COL])
    return df
  except Exception as e:
    print(f"Error in base_guard: {e}")

# Define function to compute throughput
def calculate_throughput(df: pd.DataFrame) -> pd.DataFrame:
  '''
  Function to compute throughput metrics from raw data.\n
  params:
  - df: Input dataframe with raw data.\n
  returns:
  - DataFrame with additional throughput columns.
  '''
  try:
    # Apply base guard
    df = base_guard(df)
    if df is None or df.empty:
      return df

    # Calculate throughput
    df = df.dropna(subset=["tx_total_bytes", "rx_total_bytes"])
    df["delta_t"] = df.groupby(DEVICE_COL)[TIMESTAMP_COL].diff().dt.total_seconds()
    df["delta_tx_bytes"] = df.groupby(DEVICE_COL)["tx_total_bytes"].diff()
    df["delta_rx_bytes"] = df.groupby(DEVICE_COL)["rx_total_bytes"].diff()

    # Remove rows with non-positive delta_t or NaN values
    df = df.dropna(subset=["delta_t", "delta_tx_bytes", "delta_rx_bytes"])
    
    # Calculate throughput in bps and Mbps
    df["throughput_upload_bps"] = (df["delta_tx_bytes"] * 8) / df["delta_t"]
    df["throughput_download_bps"] = (df["delta_rx_bytes"] * 8) / df["delta_t"]
    df["throughput_total_bps"] = (
      (df["delta_tx_bytes"] + df["delta_rx_bytes"]) * 8 / df["delta_t"]
    )

    # Convert to Mbps
    df["throughput_upload_mbps"] = df["throughput_upload_bps"] / 1e6
    df["throughput_download_mbps"] = df["throughput_download_bps"] / 1e6
    df["throughput_total_mbps"] = df["throughput_total_bps"] / 1e6
    return df
  except Exception as e:
    print(f"Error in calculate_throughput: {e}")

# Define function to compute energy consumption
def calculate_energy_consumption(df: pd.DataFrame) -> pd.DataFrame:
  '''
  Function to compute energy consumption from battery data.\n
  params:
  - df: Input dataframe with battery usage data.\n
  returns:
  - DataFrame with additional energy consumption columns.
  '''
  try:
    # Apply base guard
    df = base_guard(df)
    if df is None or df.empty:
      return df
    
    # Calculate energy consumption
    df["delta_t"] = df.groupby(DEVICE_COL)[TIMESTAMP_COL].diff().dt.total_seconds()
    df["batt_voltage_v"] = df["batt_voltage_mv"] / 1000.0
    df["batt_current_a"] = df["current_avg_ua"] / 1e6
    df["energy_wh"] = (df["batt_voltage_v"] * df["batt_current_a"] * df["delta_t"]) / 3600.0
    return df
  except Exception as e:
    print(f"Error in calculate_energy_consumption: {e}")

# Define function to compute throughput, energy, and BoT
def calculate_throughput_energy_and_bot(df: pd.DataFrame) -> pd.DataFrame:
  '''
  Function to compute throughput, energy consumption, and Bits over Time (BoT).\n
  params:
  - df: Input dataframe with battery usage data.\n
  returns:
  - DataFrame with throughput, energy, and BoT metrics.
  '''
  try:
    df = base_guard(df)
    if df is None or df.empty:
      return df
    
    # Calculate throughput and energy
    thr = calculate_throughput(df)
    eng = calculate_energy_consumption(df)
    
    # Merge dataframes on device and timestamp
    merged = pd.merge(
      thr[[DEVICE_COL, TIMESTAMP_COL, "throughput_total_bps", "throughput_total_mbps"]],
      eng[[DEVICE_COL, TIMESTAMP_COL, "batt_voltage_v", "energy_wh", "batt_temp_c"]],
      on=[DEVICE_COL, TIMESTAMP_COL],
      how="inner",
    ).sort_values([DEVICE_COL, TIMESTAMP_COL])
    
    # Avoid division by zero
    merged["throughput_total_bps"] = merged["throughput_total_bps"].replace(0, np.nan)
    
    # Calculate energy per bit (in Joules)
    merged["energy_per_bit_tx"] = (ALPHA_TX / merged["throughput_total_bps"]) + BETA_TX
    merged["energy_per_bit_rx"] = (ALPHA_RX / merged["throughput_total_bps"]) + BETA_RX
    merged["energy_per_bit_tx_J"] = merged["energy_per_bit_tx"] * 1e-9
    merged["energy_per_bit_rx_J"] = merged["energy_per_bit_rx"] * 1e-9
    merged["energy_per_bit_avg_J"] = (
      merged["energy_per_bit_tx_J"] + merged["energy_per_bit_rx_J"]
    ) / 2
    
    # Calculate Bits over Time (BoT) in mAh per Gbps
    V_avg = merged["batt_voltage_v"].mean()
    merged["BoT_mAh_per_Gbps"] = (
      merged["energy_per_bit_avg_J"] * (8 * 1e9) / V_avg
    ) * (1000.0 / 3600.0)
    return merged
  except Exception as e:
    print(f"Error in calculate_throughput_energy_and_bot: {e}")