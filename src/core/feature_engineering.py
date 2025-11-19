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