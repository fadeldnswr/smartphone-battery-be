'''
Module for aging feature calculations for smartphone batteries.
This module includes functions to compute aging-related features
based on battery usage data.
'''

import pandas as pd

from .config import DEVICE_COL, TIMESTAMP_COL

# Define function to compute aging features
def add_aging_features(df: pd.DataFrame, win_fast: int = 6, win_slow: int = 48) -> pd.DataFrame:
  '''
  Function to compute aging-related features for smartphone batteries.\n
  params:
  - df: Input dataframe with battery usage data.
  - win_fast: Window size for fast EMA.
  - win_slow: Window size for slow EMA.
  \nreturns:
  - DataFrame with additional aging feature columns.
  '''
  try:
    df = df.copy()
    df = df.sort_values([DEVICE_COL, TIMESTAMP_COL])
    df["SoH_filled"] = df["SoH_filled"].ffill().bfill()
    
    # Define per-device processing function
    def _per_dev(g: pd.DataFrame) -> pd.DataFrame:
      g = g.sort_values(TIMESTAMP_COL).copy()
      g["soh_ema_fast"] = g["SoH_filled"].ewm(span=win_fast, adjust=False).mean()
      g["soh_ema_slow"] = g["SoH_filled"].ewm(span=win_slow, adjust=False).mean()
      g["soh_trend"] = g["soh_ema_fast"] - g["soh_ema_slow"]
      g["efc_delta"] = g["EFC"].diff().fillna(0.0)
      
      # Temperature and throughput/energy EMA
      if "batt_temp_c" in g.columns:
        g["temp_ema"] = g["batt_temp_c"].ewm(span=win_fast, adjust=False).mean()
        g["temp_max_win"] = g["batt_temp_c"].rolling(win_fast, min_periods=1).max()
      else:
        g["temp_ema"] = 0.0
        g["temp_max_win"] = 0.0
      
      # Throughput and energy EMA
      if "throughput_total_gb" in g.columns:
        g["tp_ema"] = g["throughput_total_gb"].ewm(span=win_fast, adjust=False).mean()
      else:
        g["tp_ema"] = 0.0
      
      # Energy per bit EMA
      if "energy_per_bit_avg_J" in g.columns:
        g["epb_ema"] = g["energy_per_bit_avg_J"].ewm(span=win_fast, adjust=False).mean()
      else:
        g["epb_ema"] = 0.0
      
      return g
    # Apply per-device processing
    df = df.groupby(DEVICE_COL).apply(_per_dev).reset_index(drop=True)
    return df
  except Exception as e:
    print(f"Error in add_aging_features: {e}")