'''
Module for feature engineering tasks.
This module includes functions for scaling, encoding, and transforming features
to prepare data for machine learning models.
'''

import pandas as pd
import numpy as np

from .soh_cycles import calculate_soh_cycles
from .throughput_energy import calculate_throughput_energy_and_bot
from .aging_features import add_aging_features
from .config import DEVICE_COL, TIMESTAMP_COL

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import List, Dict, Any, Tuple

# Define base columns for aging features
AGING_BASE_COLS = [
  "batt_voltage_v",
  "batt_temp_c",
  "throughput_total_mbps",
  "energy_per_bit_avg_J",
  "SoH_filled",
  "EFC",
  "soh_trend",
  "efc_delta",
  "temp_ema",
  "temp_max_win",
  "tp_ema",
  "epb_ema",
]

# Define function to create LSTM features
def make_lstm_features(df_raw: pd.DataFrame) -> pd.DataFrame:
  '''
  Function to create features suitable for LSTM models.\n
  params:
  - df_raw: Input dataframe with raw battery usage data.\n
  returns:
  - DataFrame with engineered features for LSTM models.
  '''
  try:
    # SoH & cycles (per device)
    soh_df = df_raw.groupby(DEVICE_COL, group_keys=False).apply(
      calculate_soh_cycles
    )
    
    # Throughput + energy + epb + BoT
    te_df = calculate_throughput_energy_and_bot(df_raw)
    
    # Join sebaiknya pakai device_id + created_at
    merged = pd.merge(
      soh_df,
      te_df[
        [
          DEVICE_COL,
          TIMESTAMP_COL,
          "throughput_total_bps",
          "throughput_total_mbps",
          "energy_wh",
          "energy_per_bit_avg_J",
          "BoT_mAh_per_Gbps",
        ]
      ],
      on=[DEVICE_COL, TIMESTAMP_COL],
      how="left",
    )
    
    # Aging features buat LSTM
    feat = add_aging_features(merged)
    return feat
  except Exception as e:
    print(f"Error in make_lstm_features: {e}")

# Function to add per-device z-score normalization
def add_per_device_zscore(df, cols=AGING_BASE_COLS) -> pd.DataFrame:
  try:
    df = df.copy()
    def _z_per_dev(g):
      for c in cols:
        if c not in g.columns:
          continue
        x = g[c].astype(float)
        mu = x.mean()
        sigma = x.std(ddof=0)
        if sigma == 0 or np.isnan(sigma):
          g[c + "_z"] = 0.0
        else:
          g[c + "_z"] = (x - mu) / sigma
      return g
    df = df.groupby("device_id", group_keys=False).apply(_z_per_dev)
    return df
  except Exception as e:
    print(f"Error in add_per_device_zscore: {e}")

# Define function to build windows
def build_windows(
  df_feat: pd.DataFrame, feature_cols: List[str], 
  target_col: str, win_size: int, 
  soh_true_col: str = "SoH_smooth") -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
  '''
  Function to build sliding windows for LSTM input.\n
  params:
  - df: Input dataframe with features and target.\n
  - feature_cols: List of feature column names.\n
  - target_col: Name of the target column.\n
  - win_size: Size of the sliding window.\n
  - soh_true_col: Name of the SoH true column.\n
  returns:
  - Tuple of numpy arrays: (X_windows, y_targets, timestamps, soh_true_values).
  '''
  try:
    # Choose SoH true
    if soh_true_col in df_feat.columns:
      soh_true_series = df_feat[soh_true_col].astype(float) * 100.0
    elif "SoH_pct" in df_feat.columns:
      soh_true_series = df_feat["SoH_pct"].astype(float)
    else:
      raise ValueError("No valid SoH true column found.")
    
    # Define values
    values = df_feat[feature_cols].values
    n = len(values)
    
    # Define lists for windows
    windows = []
    timestamps = []
    soh_true_list = []
    efc_list = []
    
    # Create sliding windows
    for i in range(win_size, n):
      win = values[i - win_size : i]
      windows.append(win)
      timestamps.append(df_feat["created_at"].iloc[i])
      soh_true_list.append(float(soh_true_series.iloc[i]))
      efc_list.append(float(df_feat["EFC"].iloc[i]) if "EFC" in df_feat.columns else np.nan)
    
    # Create numpy arrays
    X = np.array(windows, dtype=float)
    timestamps = np.array(timestamps)
    soh_true_arr = np.array(soh_true_list, dtype=float)
    efc_arr = np.array(efc_list, dtype=float)
    
    # Return arrays
    return X, timestamps, soh_true_arr, efc_arr
  except Exception as e:
    print(f"Error in build_windows: {e}")