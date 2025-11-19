'''
Utility functions for the smartphone battery notebook project.
Includes functions for data processing, visualization, and model evaluation.
'''

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error
from psycopg2 import connect

# Define function to create postgres connection
def connect_to_db(host, port, db_name, user, password):
  try:
    # Create connection
    conn = connect(
      host=host,
      port=port,
      dbname=db_name,
      user=user,
      password=password
    )
    # Check if connection created successfully
    if conn:
      print("Connection to database established successfully.")
    else:
      print("Failed to establish connection to database.")
    return conn
  except Exception as e:
    print(f"Error connecting to database: {e}")

# Define battery capacity spec for each devices
BATTERY_CAPACITY_SPEC = {
  "SM-S931B-57bc0e2d9eac7750": 4090,
  "SM-A556E-7ecd175336df7fc4": 5000,
  "SM-A556E-5f0400c50aae82ca": 5000,
  "V2050-b202c09b34bc8540": 4000,
  "SM-T505-280eb41faa621df0": 7040,
  "SM-A546E-8af17d67f9288898": 5000,
  "SM-A725F-6698366a2e3a4ff1": 5000,
  "2311DRK48G-b135dcd1d7e9320f": 5000,
  "SM-A546E-701861f29b4d5913": 5000,
  "SM-A155F-7d69b63bc200801a": 5000,
  "SM-A336E-c89e0bb491fe3651": 5000,
  "SM-A336E-c471046323c8859c": 5000,
  "Infinix X6886-e495e4491a5c2a82": 5160,
  "SM-A356E-4e32dd36015962aa": 5000,
  "SM-S921B-d2c3f5675ad3a14d": 4000,
  "SM-S926B-1ccc6862dc88e6b9": 4900,
  "Infinix X669C-a1b2d29d54d19af3": 4900,
  "SM-S916B-205d95c2abec51c0": 4700,
  "22021211RG-0940e2943d7b49eb": 4500,
  "SM-A546E-1cf82eec40a3542b": 5000,
  "Redmi Note 9 Pro-d2c7435268ff2367": 5020,
  "24117RN76O-af9a140a5e0ea0de": 5500,
  "2406APNFAG-4b17a6ddf26cd705": 5000,
  "2312DRA50G-223024e791e6150d": 5100,
  "SM-S911B-aee10fcb8586030e": 3900,
}

def _hampel(s: pd.Series, k: int = 7, nsigma: float = 5.0) -> pd.Series:
  s = s.copy()
  med = s.rolling(window=2*k+1, center=True, min_periods=3).median()
  mad = (s - med).abs().rolling(window=2*k+1, center=True, min_periods=3).median()
  thresh = nsigma * 1.4826 * mad
  outlier = (s - med).abs() > thresh
  s[outlier] = np.nan
  return s.interpolate(limit_direction="both")


# Create function to calculate SoH and battery cycles
def calculate_soh_and_cycles(
  df: pd.DataFrame, capacity_map: dict = BATTERY_CAPACITY_SPEC, 
  default_C0: int = 5000, threshold: int = 100, roll_win: int = 3) -> pd.DataFrame:
  try:
    # Prepare dataframe
    df = df.copy() 
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.sort_values("created_at").reset_index(drop=True)
    
    # Time for each sample
    df["delta_t_s"] = df["created_at"].diff().dt.total_seconds().fillna(0)
    df.loc[df["delta_t_s"] < 0, "delta_t_s"] = 0
    df.loc[df["delta_t_s"] > 3600, "delta_t_s"] = 0 
    
    # C_nom for battery capacity
    model = df["device_id"].iloc[0] if "device_id" in df.columns else None
    C_nom_spec = None
    if capacity_map is not None and model is not None:
      C_nom_spec = capacity_map.get(model)

    # Check available data columns
    use_charge_counter = "charge_counter" in df.columns and df["charge_counter"].notna().any()
    use_current_avg    = "current_avg_ua" in df.columns and df["current_avg_ua"].notna().any()
    
    # Check if no useful data available
    if use_charge_counter:
      # Asumsi charge_counter dalam µAh -> konversi ke mAh
      df["Q_mAh"] = df["charge_counter"] / 1000.0
      df["Q_mAh_raw"] = df["Q_mAh"]
      df["Q_mAh"] = _hampel(df["Q_mAh"], k=7, nsigma=5.0)
      
      # Check if median Q_mAh is negative, if so invert the sign
      if df["Q_mAh"].dropna().median() < 0:
        df["Q_mAh"] = -df["Q_mAh"]
    
    # Use current_avg_ua to estimate capacity
    elif use_current_avg:
      df["batt_current_a"] = df["current_avg_ua"] / 1e6
      df["delta_Q_Ah"] = df["batt_current_a"] * df["delta_t_s"] / 3600.0
      df["Q_Ah"] = df["delta_Q_Ah"].cumsum()
      df["Q_Ah"] = df["Q_Ah"] - df["Q_Ah"].min()
      df["Q_mAh"] = df["Q_Ah"] * 1000.0
    
    # No useful data available
    else:
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
    
    # Ct_mAh calculation from blocks of full charges
    full_thresh = max(threshold - 1, 98)
    df["battery_level"] = pd.to_numeric(df["battery_level"], errors="coerce")
    df["is_full"] = (df["battery_level"] >= full_thresh).astype(int)
    block_id = (df["is_full"].ne(df["is_full"].shift(1))).cumsum()
    df["full_block_id"] = np.where(df["is_full"] == 1, block_id, np.nan)
    
    df["Ct_mAh"] = np.nan
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
      df["Ct_mAh"] = (
        df["Q_mAh"]
        .rolling(window=6, min_periods=3)
        .max()
      )
    
    if C_nom_spec is not None:
      df["Ct_mAh"] = df["Ct_mAh"].clip(lower=0.70 * C_nom_spec ,upper=1.15 * C_nom_spec)
    
    df["Ct_mAh"] = df["Ct_mAh"].ffill()
    
    # SoH calculation and smoothing
    valid_ct = df["Ct_mAh"].dropna()
    if not valid_ct.empty:
      hi = np.nanpercentile(valid_ct, 99)
      valid_ct = valid_ct[valid_ct <= hi]
      C0_ref_data = float(np.percentile(valid_ct, 95))
    
    # Check C0_ref from spec or default
    if C_nom_spec is not None and C0_ref_data is not None:
      C0_ref = float(np.clip(C0_ref_data, 0.95 * C_nom_spec, 1.05 * C_nom_spec))
    elif C0_ref_data is not None:
      C0_ref = float(C0_ref_data)
    elif C_nom_spec is not None:
      C0_ref = float(C_nom_spec)
    else:
      C0_ref = float(default_C0)
    
    df["SoH"] = (df["Ct_mAh"] / C0_ref).clip(lower=0.0, upper=1.2)
    df["SoH_smooth"] = df["SoH"].rolling(roll_win, min_periods=1, center=True).median()
    df["SoH_pct"] = df["SoH"] * 100.0
    df["SoH_smooth_pct"] = df["SoH_smooth"] * 100.0
    
    # Calculate EFC from discharge cycles
    df["delta_Q_mAh"] = df["Q_mAh"].diff().fillna(0)
    df["discharge_mAh"] = np.where(df["delta_Q_mAh"] < 0, -df["delta_Q_mAh"], 0.0)
    
    q99 = df["discharge_mAh"].quantile(0.99)
    df.loc[df["discharge_mAh"] > q99, "discharge_mAh"] = q99
    df["EFC"] = df["discharge_mAh"].cumsum() / C0_ref
    
    return df
  except Exception as e:
    print(f"Error calculating SoH and cycles: {e}")

def count_non_null_per_devices(df: pd.DataFrame, cols, name):
  print(f"\n=== {name} ===")
  out = (
    df.groupby("device_id")[cols]
    .apply(lambda g: g.notna().all(axis=1).sum())
    .rename("valid_rows")
  )
  print(out.sort_values(ascending=False))
  print("Devices with >=1 valid row:", (out>0).sum(), "of", out.shape[0])

# Define function to drop devices
def quarantine_device(df: pd.DataFrame):
  bad = []
  for dev, g in df.groupby("device_id"):
    s = g ["SoH_filled"].dropna()
    if s.empty:
      bad.append(dev); continue
    if (s.max() > 1.2) or (s.min() < 0):
      bad.append(dev); continue
    
    # Example ct criteria
    C_nom = BATTERY_CAPACITY_SPEC.get(dev, 5000)
    ct = g["Ct_mAh"].dropna()
    if not ct.empty and ((ct > 1.15*C_nom).mean() > 0.05 or (ct < 0.7*C_nom).mean() > 0.05 ):
      bad.append(dev); continue
    
    dq = g["Q_mAh"].diff().abs().dropna()
    if not dq.empty and dq.quantile(0.99) > 0.4 * C_nom:
      bad.append(dev); continue
  return sorted(set(bad))

# 3) Fungsi plot per-device: SoH(%) vs waktu
def plot_device_time(res_df, device_id, outdir="exports/plots_pred"):
  os.makedirs(outdir, exist_ok=True)
  g = (res_df[res_df["device_id"] == device_id]
    .sort_values("created_at"))
  if g.empty:
    print(f"[skip] {device_id}: no rows")
    return None

  # hitung MAE dev untuk anotasi
  mae_d = mean_absolute_error(g["SoH_true"], g["SoH_pred"])
  rmse_d = np.sqrt(mean_squared_error(g["SoH_true"], g["SoH_pred"]))

  plt.figure(figsize=(10,4))
  plt.plot(g["created_at"], g["SoH_true"]*100, label="SoH True (%)")
  plt.plot(g["created_at"], g["SoH_pred"]*100, label="SoH Pred (%)", alpha=0.9)
  plt.ylabel("SoH (%)"); plt.xlabel("Time"); plt.grid(True, alpha=0.25)
  plt.title(f"SoH True vs Pred — {device_id}\nMAE={mae_d:.4f}, RMSE={rmse_d:.4f}")
  plt.legend(loc="best")
  fname = os.path.join(outdir, f"{device_id}_soh_pred_vs_true_time.png")
  plt.tight_layout(); plt.savefig(fname); plt.close()
  return fname

# 4) Fungsi plot kurva degradasi: SoH(%) vs EFC jika kamu punya EFC_test selaras
def plot_device_degradation_with_merge(res_df, df_all, device_id, outdir="exports/plots_pred"):
  os.makedirs(outdir, exist_ok=True)
  g = (res_df[res_df["device_id"] == device_id]
    .sort_values("created_at"))
  if g.empty:
    print(f"[skip] {device_id}: no rows")
    return None

  base = (df_all.loc[df_all["device_id"] == device_id, ["device_id","created_at","EFC"]]
    .copy())
  base["created_at"] = pd.to_datetime(base["created_at"], errors="coerce")
  gm = pd.merge_asof(
    g.sort_values("created_at"),
    base.sort_values("created_at"),
    on="created_at", by="device_id", direction="nearest", tolerance=pd.Timedelta("5min")
  )
  gm = gm.dropna(subset=["EFC"])
  if gm.empty:
    print(f"[skip] {device_id}: no EFC aligned")
    return None

  plt.figure(figsize=(8,4))
  plt.plot(gm["EFC"], gm["SoH_true"]*100, label="True")
  plt.plot(gm["EFC"], gm["SoH_pred"]*100, label="Pred", alpha=0.9)
  plt.xlabel("EFC"); plt.ylabel("SoH (%)"); plt.grid(True, alpha=0.3)
  plt.title(f"Degradation Curve (True vs Pred) — {device_id}")
  plt.legend(loc="best")
  fname = os.path.join(outdir, f"{device_id}_soh_pred_vs_true_vs_efc.png")
  plt.tight_layout(); plt.savefig(fname); plt.close()
  return fname

# Define function to add aging features
def add_aging_features(df, win_fast=6, win_slow=48):
  df = df.copy()
  df = df.sort_values(["device_id", "created_at"])
  df["SoH_filled"] = df["SoH_filled"].ffill().bfill()
  
  def _per_dev(g):
    g = g.sort_values("created_at").copy()
    # EMA SoH
    g["soh_ema_fast"] = g["SoH_filled"].ewm(span=win_fast, adjust=False).mean()
    g["soh_ema_slow"] = g["SoH_filled"].ewm(span=win_slow, adjust=False).mean()
    
    # trend (positif = naik, negatif = turun)
    g["soh_trend"] = g["soh_ema_fast"] - g["soh_ema_slow"]
    
    # delta EFC
    g["efc_delta"] = g["EFC"].diff().fillna(0.0)
    
    # temperature features
    if "batt_temp_c" in g.columns:
      g["temp_ema"] = g["batt_temp_c"].ewm(span=win_fast, adjust=False).mean()
      g["temp_max_win"] = g["batt_temp_c"].rolling(win_fast, min_periods=1).max()
    else:
      g["temp_ema"] = 0.0
      g["temp_max_win"] = 0.0
    # throughput features
    if "throughput_total_gb" in g.columns:
      g["tp_ema"] = g["throughput_total_gb"].ewm(span=win_fast, adjust=False).mean()
    else:
      g["tp_ema"] = 0.0
    if "energy_per_bit_avg_J" in g.columns:
      g["epb_ema"] = g["energy_per_bit_avg_J"].ewm(span=win_fast, adjust=False).mean()
    else:
      g["epb_ema"] = 0.0
    return g
  df = df.groupby("device_id").apply(_per_dev).reset_index(drop=True)
  return df