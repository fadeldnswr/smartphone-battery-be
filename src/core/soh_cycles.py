'''
Module for calculating State of Health (SoH) cycles for smartphone batteries.
This module includes functions to compute SoH based on battery usage data
and to identify charge-discharge cycles.
'''

import numpy as np
import pandas as pd

from .config import BATTERY_CAPACITY_SPEC, TIMESTAMP_COL, DEVICE_COL

# Define function to identify cycles using Hampel filter
def _hampel(s: pd.Series, k: int = 7, nsigma: float = 5.0):
  '''
  Function to apply Hampel filter to a pandas Series to identify and remove outliers.\n
  params:
  - s: Input pandas Series.
  - k: Window size parameter.
  - nsigma: Number of standard deviations to use as threshold.
  '''
  try:
    # Copy series
    s = s.copy()
    med = s.rolling(window=2 * k + 1, center=True, min_periods=3).median()
    mad = (s - med).abs().rolling(window=2*k+1, center=True, min_periods=3).median()
    thresh = nsigma * 1.4826 * mad
    outlier = (s - med).abs() > thresh
    s[outlier] = np.nan
    return s
  except Exception as e:
    print(f"Error in _hampel: {e}")
    return s

# Define function to compute SoH cycles
def calculate_soh_cycles(
  df: pd.DataFrame, capacity_map: dict = BATTERY_CAPACITY_SPEC, 
  default_C0: int = 5000, threshold: float = 100, roll_win: int = 3) -> pd.DataFrame:
  '''
  Function to compute State of Health (SoH) cycles for smartphone batteries.\n
  params:
  - df: Input dataframe with battery usage data.
  - capacity_map: Dictionary mapping device IDs to their nominal battery capacities (in mAh).
  - default_C0: Default nominal capacity (in mAh) if device ID not found in capacity_map.
  - threshold: Minimum discharge (in mAh) to consider a cycle.
  - roll_win: Window size for rolling average to smooth SoH values.
  returns:
  - DataFrame with additional 'SoH' column representing State of Health cycles.
  '''
  try:
    # Copy and sort dataframe
    df = df.copy()
    df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL], errors="coerce")
    df = df.sort_values([DEVICE_COL, TIMESTAMP_COL]).reset_index(drop=True)

    # delta_t per sample
    df["delta_t_s"] = df.groupby(DEVICE_COL)[TIMESTAMP_COL].diff().dt.total_seconds()
    df["delta_t_s"] = df["delta_t_s"].fillna(0)
    df.loc[df["delta_t_s"] < 0, "delta_t_s"] = 0
    df.loc[df["delta_t_s"] > 3600, "delta_t_s"] = 0

    # C_nom per device 
    model = df[DEVICE_COL].iloc[0] if DEVICE_COL in df.columns else None
    C_nom_spec = capacity_map.get(model) if model is not None else None
    
    # Check available data for SoH calculation
    use_charge_counter = (
      ("charge_counter_uah" in df.columns and df["charge_counter_uah"].notna().any())
      or ("charge_counter" in df.columns and df["charge_counter"].notna().any())
    )
    use_current_avg = "current_avg_ua" in df.columns and df["current_avg_ua"].notna().any()
    
    if use_charge_counter:
      if "charge_counter_uah" in df.columns:
        raw = df["charge_counter_uah"]
      else:
        raw = df["charge_counter"] 
      df["Q_mAh"] = pd.to_numeric(raw, errors="coerce") / 1000.0
      df["Q_mAh_raw"] = df["Q_mAh"]
      df["Q_mAh"] = _hampel(df["Q_mAh"], k=7, nsigma=5.0)
        
      # If median Q_mAh negatif, invert values
      if df["Q_mAh"].dropna().median() < 0:
        df["Q_mAh"] = -df["Q_mAh"]
      
    elif use_current_avg:
      df["batt_current_a"] = df["current_avg_ua"] / 1e6
      df["delta_Q_Ah"] = df["batt_current_a"] * df["delta_t_s"] / 3600.0
      df["Q_Ah"] = df["delta_Q_Ah"].cumsum()
      df["Q_Ah"] = df["Q_Ah"] - df["Q_Ah"].min()
      df["Q_mAh"] = df["Q_Ah"] * 1000.0
    else:
      # Fallback if no data available
      df["Q_mAh"] = np.nan
      df["Ct_mAh"] = np.nan
      df["SoH"] = np.nan
      df["SoH_smooth"] = np.nan
      df["SoH_pct"] = np.nan
      df["SoH_smooth_pct"] = np.nan
      df["delta_Q_mAh"] = np.nan
      df["discharge_mAh"] = np.nan
      df["EFC"] = np.nan
      return df
    
    # Ct_mAh calculation
    full_thresh = max(threshold - 1, 98)
    df["battery_level"] = pd.to_numeric(df["battery_level"], errors="coerce")
    df["is_full"] = (df["battery_level"] >= full_thresh).astype(int)
    block_id = (df["is_full"].ne(df["is_full"].shift(1))).cumsum()
    df["full_block_id"] = np.where(df["is_full"] == 1, block_id, np.nan)
    df["Ct_mAh"] = np.nan
    
    # Calculate Ct_mAh per full charge block
    if df["full_block_id"].notna().any():
      grp = df.dropna(subset=["full_block_id", "Q_mAh"])
      for bid, g in grp.groupby("full_block_id"):
        q = g["Q_mAh"].dropna()
        if q.empty:
          continue
        ct = np.nanpercentile(q, 95)
        idx = q.idxmax()
        df.loc[idx, "Ct_mAh"] = ct
      
    if df["Ct_mAh"].isna().all():
      df["Ct_mAh"] = df["Q_mAh"].rolling(window=6, min_periods=3).max()
    
    if C_nom_spec is not None:
      df["Ct_mAh"] = df["Ct_mAh"].clip(
        lower=0.70 * C_nom_spec, upper=1.15 * C_nom_spec
      )
    df["Ct_mAh"] = df["Ct_mAh"].ffill()
    
    # C0_ref from data + spec
    valid_ct = df["Ct_mAh"].dropna()
    C0_ref_data = None
    if not valid_ct.empty:
      hi = np.nanpercentile(valid_ct, 99)
      valid_ct = valid_ct[valid_ct <= hi]
      C0_ref_data = float(np.percentile(valid_ct, 95))
    
    # Determine C0_ref
    if C_nom_spec is not None and C0_ref_data is not None:
      C0_ref = float(np.clip(C0_ref_data, 0.95 * C_nom_spec, 1.05 * C_nom_spec))
    elif C0_ref_data is not None:
      C0_ref = float(C0_ref_data)
    elif C_nom_spec is not None:
      C0_ref = float(C_nom_spec)
    else:
      C0_ref = float(default_C0)
    
    # SoH calculations
    df["SoH"] = (df["Ct_mAh"] / C0_ref).clip(lower=0.0, upper=1.2)
    df["SoH_smooth"] = (
      df["SoH"].rolling(roll_win, min_periods=1, center=True).median()
    )
    df["SoH_pct"] = df["SoH"] * 100.0
    df["SoH_smooth_pct"] = df["SoH_smooth"] * 100.0
    
    # EFC
    df["delta_Q_mAh"] = df["Q_mAh"].diff().fillna(0)
    df["discharge_mAh"] = np.where(df["delta_Q_mAh"] < 0, -df["delta_Q_mAh"], 0.0)
    
    # Cap discharge_mAh at 99th percentile to avoid outliers
    q99 = df["discharge_mAh"].quantile(0.99)
    df.loc[df["discharge_mAh"] > q99, "discharge_mAh"] = q99
    df["EFC"] = df["discharge_mAh"].cumsum() / C0_ref
    
    return df
  except Exception as e:
    print(f"Error in calculate_soh_cycles: {e}")
    return pd.DataFrame()