'''
Module for prediction controller functions
'''

import os
import sys
import numpy as np
import json
import pickle
import math

from src.logging.logging import logging
from src.exception.exception import CustomException
from src.pipeline.data_ingestion import DataIngestion
from src.pipeline.data_transformation import DataTransformation
from src.api.model.prediction_model import PredictionResponse

from tensorflow.keras.models import load_model
from typing import Dict, Any
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Define model directory
MODEL_DIR = os.getenv("MODEL_DIR")

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
    df_raw = DataIngestion(table_name="raw_metrics", device_id=device_id).extract_data_from_db()
    logging.info(f"RAW COLUMNS: {df_raw.columns.tolist()}")
    logging.info(f"RAW HEAD:\n{df_raw.head(5)}")

    # Check if df_raw is empty
    if df_raw is None or len(df_raw) == 0:
      raise ValueError("No data found for the device.")
    
    # Compute metrics
    df_metrics = DataTransformation(data=df_raw).compute_metrics()
    logging.info(f"Metrics data shape {df_metrics.shape} for device {device_id}")
    
    # Ensure soh true column exists
    soh_true_col = "soh_smooth" if "soh_smooth" in df_metrics.columns else "soh_pct"
    
    # Build sliding windows for prediction
    values = df_metrics[feature_cols].values
    n = len(values)
    
    # Define list of sliding windows
    windows = []
    timestamps = []
    soh_true_list = []
    
    # Create sliding window algorithm
    for i in range(win_size, n):
      win = values[i - win_size : i]
      windows.append(win)
      timestamps.append(df_metrics["created_at"].iloc[i])
      soh_true_list.append(float(df_metrics[soh_true_col].iloc[i]) * 100.0)
    
    # Scaled input features
    X = np.array(windows)
    X_scaled = scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
    soh_pred_arr = model.predict(X_scaled).reshape(-1) * 100.0
    
    # Last point for summary
    soh_pred_last = float(soh_pred_arr[-1]) / 100
    soh_pred_pct_last = float(soh_pred_arr[-1])
    
    # Estimate remaining useful life from soh prediction
    rul_dict = estimate_rul_from_soh(soh_pred=soh_pred_last)
    
    # Define soh series
    soh_series = []
    for t, soh_t, soh_p in zip(timestamps, soh_true_list, soh_pred_arr):
      soh_series.append({
        "created_at": t,
        "soh_true": float(soh_t),
        "soh_pred": float(soh_p)
      })
    
    return PredictionResponse(
      message="Prediction successful",
      device_id=device_id,
      soh_pred_pct=safe_float(soh_pred_pct_last, 0.0),
      soh_pred=safe_float(soh_pred_last, 0.0),
      rul_cycles=safe_float(rul_dict["rul_cycles"], 0.0),
      rul_months=safe_float(rul_dict["rul_months"], 0.0),
      rul_hours=safe_float(rul_dict["rul_hours"], 0.0),
      soh_series=soh_series
    )
  except Exception as e:
    logging.error(f"Error in run_prediction_pipeline: {e}")
    raise CustomException(e, sys)

# Define safe float controller
def safe_float(x) -> float:
  '''
  Function to safely convert input to float, returning 0.0 for NaN or infinite values.\n
  params:
  - x: Input value to convert.
  returns:
  - float: Converted float value or 0.0.
  '''
  try:
    x = float(x)
  except Exception as e:
    return 0.0
  if math.isnan(x) or math.isinf(x):
    return 0.0
  return x