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