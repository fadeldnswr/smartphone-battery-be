'''
Module for prediction controller functions
'''

import os
import sys
import numpy as np
import json
import pickle
import math
import pandas as pd

from src.logging.logging import logging
from src.exception.exception import CustomException
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation
from src.api.model.prediction_model import PredictionResponse
from src.service.expiry_date_calculation import compute_expiry_date

from tensorflow.keras.models import load_model
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from typing import Dict, Any
from dotenv import load_dotenv
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Define model directory
MODEL_DIR = os.getenv("MODEL_DIR")

# Define max rows to process
MAX_ROWS = 500

if not MODEL_DIR:
    raise RuntimeError("MODEL_DIR is not set. Check your .env and ENV_PATH configuration.")

model_path = os.path.join(f"{MODEL_DIR}/latest", "model.keras")
scaler_path = os.path.join(f"{MODEL_DIR}/latest", "scaler.pkl")

if not os.path.exists(model_path):
    raise RuntimeError(f"Model file not found at {model_path}")

if not os.path.exists(scaler_path):
    raise RuntimeError(f"Scaler file not found at {scaler_path}")

# Load model
model = load_model(model_path, compile=False)

# Open scaler
with open(scaler_path, "rb") as file:
  scaler = pickle.load(file=file)

# Open JSON file configuration
config_path = os.path.join(f"{MODEL_DIR}/latest", "config.json")
with open(config_path, "r") as file:
  model_config = json.load(file)

# Feature and target columns
win_size = model_config["window_size"]
feature_cols = model_config["feature_cols"]
target_col = model_config["target_col"]

# RUL configuration
rul_config = model_config["rul_config"]
k_global = model_config["rul_config"]["k_global"]
soh_eol = model_config["rul_config"]["soh_eol"] 
hours_per_cycle = model_config["rul_config"]["hours_per_cycle"]

# Define function to estimate RUL from SoH
def estimate_rul_from_soh(soh_pred: float) -> Dict[str, Any]:
  '''
  Estimate RUL in months from predicted SoH percentage.\n
  params:
  - soh_pred (float): Predicted State of Health in percentage (0-100).
  returns:
  - dict: Dictionary with estimated RUL in months.
  '''
  try:
    delta_soh = soh_pred - soh_eol
    rul_cycles = max(delta_soh / k_global, 0)
    
    # Convert RUL cycles to months
    rul_hours = rul_cycles * hours_per_cycle
    rul_days = rul_hours / 24.0
    rul_months = rul_days / 30.0
    rul_years = rul_days / 365.0 
    
    # Return RUL estimates
    return {
      "rul_cycles": rul_cycles,
      "rul_hours": rul_hours,
      "rul_months": rul_months,
      "rul_years": rul_years
    }
  except Exception as e:
    logging.error(f"Error in estimate_rul_from_soh: {e}")
    raise CustomException(e, sys)

# Define function to compute evaluation metrics
def compute_eval_metrics(y_true, y_pred) -> Dict[str, Any]:
  try:
    # Define metrics
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if mask.sum() < 2:
      return { "mae_pct": None, "rmse_pct": None, "r2_soh": None }
    
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    # Define evaluation metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    return {
      "mae_pct": mae,
      "rmse_pct": rmse,
      "r2_soh": r2
    }
  except Exception as e:
    logging.error(f"Error in compute_eval_metrics: {e}")
    raise CustomException(e, sys)

# Define function to run prediction pipeline
def run_prediction_pipeline(device_id: str) -> PredictionResponse:
  '''
  Function to run the prediction pipeline for a given device ID.\n
  params:
  - device_id (str): Device ID for which to run the prediction.
  returns:
  - dict: Dictionary with prediction results.
  '''
  try:
    # Load raw metrics
    df_raw = DataIngestion(table_name="raw_metrics", device_id=device_id).extract_data_from_db(limit=20000)
    logging.info(f"RAW COLUMNS: {df_raw.columns.tolist()}")
    logging.info(f"RAW HEAD:\n{df_raw.head(5)}")

    # Check if df_raw is empty
    if df_raw is None or len(df_raw) == 0:
      raise ValueError("No data found for the device.")
    
    # Compute metrics
    df_metrics = DataTransformation(data=df_raw).compute_metrics()
    logging.info(f"Metrics data shape {df_metrics.shape} for device {device_id}")
    
    df_metrics = pd.get_dummies(df_metrics, columns=["fg_pkg"], prefix="app")
    for col in feature_cols:
      if col not in df_metrics.columns:
        if col.startswith("app_"):
          df_metrics[col] = 0.0
        else:
          logging.warning(f"Feature column {col} not found in metrics data. Filling with NaN.")
    
    extra_app_cols = [c for c in df_metrics.columns if c.startswith("app_") and c not in feature_cols]
    if extra_app_cols:
      df_metrics = df_metrics.drop(columns=extra_app_cols)
    
    # Check missing cols
    required_cols = feature_cols + [target_col]
    
    df_feat = df_metrics.copy()
    df_feat = df_feat.dropna(subset=feature_cols + [target_col])
    df_feat = (
      df_feat
      .sort_values(["device_id", "created_at"])    
      .groupby("device_id")
      .head(MAX_ROWS)   
      .reset_index(drop=True)
    )
    
    logging.info(f"FIRST TIMESTAMP API: {df_raw['created_at'].min()}")
    logging.info(f"LAST TIMESTAMP API: {df_raw['created_at'].max()}")
    logging.info(f"N API SAMPLES: {len(df_raw)}")
    logging.info(f"Feature columns: {feature_cols}")
    logging.info(f"Feature columns to list: {df_metrics.columns.to_list()}")
    
    # Ensure soh true column exists
    soh_true_col = target_col
    
    # Build sliding windows for prediction
    values = df_feat[feature_cols].values
    n = len(values)
    
    # Define list of sliding windows
    windows = []
    timestamps = []
    soh_true_list = []
    
    # Create sliding window algorithm
    for i in range(win_size, n):
      win = values[i - win_size : i]
      windows.append(win)
      timestamps.append(df_feat["created_at"].iloc[i])
      soh_true_list.append(float(df_feat[soh_true_col].iloc[i]) * 100.0)
    
    # Scaled input features
    X = np.array(windows)
    X_scaled = scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
    soh_pred_arr = model.predict(X_scaled).reshape(-1) * 100.0
    soh_pred_smooth_arr = (
      pd.Series(soh_pred_arr)
      .rolling(window=7, min_periods=1, center=True)
      .mean()
      .to_numpy()
    )
    
    # Last point for summary
    soh_pred_pct_last = safe_float(soh_pred_smooth_arr[-1], 0.0, field="soh_pred_pct_last") or 0.0
    soh_pred_last = soh_pred_pct_last / 100.0
    
    # Estimate remaining useful life from soh prediction
    rul_dict = estimate_rul_from_soh(soh_pred=soh_pred_last)
    
    # Compute expiry date
    expiry_date = compute_expiry_date(rul_months=rul_dict["rul_months"])
    
    # Extract battery cycles
    if "EFC" in df_feat.columns:
      battery_cycles = df_feat["EFC"].dropna().max()
      battery_cycles = safe_float(battery_cycles, None, field="battery_cycles")
    else:
      battery_cycles = None
    
    # Define soh series
    soh_series = []
    for t, soh_t, soh_p, index in zip(timestamps, soh_true_list, soh_pred_arr, range(len(timestamps))):
      # Take EFC for this point
      efc_val = df_feat["EFC"].iloc[win_size + index] if "EFC" in df_feat.columns else None
      soh_series.append({
        "created_at": t,
        "soh_true": safe_float(soh_t, 0.0, field="soh_true"),
        "soh_pred": safe_float(soh_p, 0.0, field="soh_pred"),
        "efc": safe_float(efc_val, None, field="efc")
      })
    
    # Compute evaluation metrics
    metrics = compute_eval_metrics(soh_true_list, soh_pred_arr)
    
    logging.info(
      f"SoH_true stats (API) – min: {np.min(soh_true_list):.4f}, "
      f"max: {np.max(soh_true_list):.4f}, std: {np.std(soh_true_list):.4f}"
    )
    logging.info(
      f"SoH_pred stats (API) – min: {np.min(soh_pred_arr):.4f}, "
      f"max: {np.max(soh_pred_arr):.4f}, std: {np.std(soh_pred_arr):.4f}"
    )

    
    return PredictionResponse(
      message="Prediction successful",
      device_id=device_id,
      soh_pred_pct=soh_pred_pct_last,
      soh_pred=soh_pred_last,
      rul_cycles=safe_float(rul_dict["rul_cycles"], 0.0, field="rul_cycles"),
      rul_months=safe_float(rul_dict["rul_months"], 0.0, field="rul_months"),
      rul_hours=safe_float(rul_dict["rul_hours"], 0.0, field="rul_hours"),
      soh_series=soh_series,
      expiry_date=expiry_date,
      mae_pct=safe_float(metrics["mae_pct"], None, "mae_pct"),
      rmse_pct=safe_float(metrics["rmse_pct"], None, "rmse_pct"),
      r2_soh=safe_float(metrics["r2_soh"], None, "r2_soh")
    )
  except Exception as e:
    logging.error(f"Error in run_prediction_pipeline: {e}")
    raise CustomException(e, sys)

# Define safe float controller
def safe_float(x: Any, default: float | None = 0.0, field:str | None = None):
  '''
  Function to safely convert input to float, returning 0.0 for NaN or infinite values.\n
  params:
  - x: Input value to convert.
  - default (float): Default value to return if conversion fails or value is invalid.
  - field (str): Optional field name for logging purposes.
  '''
  try:
    # Check if x is None
    if x is None:
      return default
    
    # Convert to float and check for inf or NaN
    v = float(x)
    if math.isinf(v) or math.isnan(v):
      if field:
        logging.warning(f"Invalid float value for field {field}: {x}. Returning default {default}.")
      return default
    return v
  except Exception:
    if field:
      logging.warning(f"Error converting field {field} value {x} to float. Returning default {default}.")
    return default