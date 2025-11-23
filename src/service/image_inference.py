'''
Modules for image inference services.
'''

import os
import sys
import json
import numpy as np

from typing import List, Dict, Any
from PIL import Image
from tensorflow.keras.models import load_model

from src.logging.logging import logging
from src.exception.exception import CustomException

# Load model and configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGE_MODEL_DIR = os.path.join(f"{BASE_DIR}/notebooks", "models", "image", "latest")
MODEL_PATH = os.path.join(IMAGE_MODEL_DIR, "model.keras")
CONFIG_PATH = os.path.join(IMAGE_MODEL_DIR, "config.json")

# Check if model and config path exists
if not os.path.exists(MODEL_PATH):
  raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

if not os.path.exists(CONFIG_PATH):
  raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")

# Open config file
with open(CONFIG_PATH, "r") as config_file:
  config = json.load(config_file)

# Load the config file parameters
IMG_H = int(config.get("image_height", 224))
IMG_W = int(config.get("image_width", 224))
CHANNELS = int(config.get("channels", 3))
RESCALE = float(config.get("rescale", 1.0/255.0))

# Load the label params from config file
LABELS = config.get("labels", ["broken", "safe", "warning"])
CLASS_INDICES = config.get("class_indices", {"broken": 0, "safe": 1, "warning": 2})
IDX_TO_LABEL = config.get("idx_to_label", None)

# Convert index to label
if IDX_TO_LABEL:
  IDX_TO_LABEL = {int(k): v for k, v in IDX_TO_LABEL.items()}
else:
  IDX_TO_LABEL = {idx: lbl for lbl, idx in CLASS_INDICES.items()}

REP_SCORE_MAP = config.get("rep_score_map", {"safe": 10, "warning": 50, "broken": 90})
SEVERITY_WEIGHTS = config.get("severity_weights", {"safe": 0.0, "warning": 0.3, "broken": 0.7})
BUCKET_THRESHOLDS = config.get("bucket_thresholds", {"safe_max": 30.0, "warning_max": 70.0})

# Simple mapping to bucket UI
_UI_BUCKET_MAP = {
  "safe": "safe",
  "warning": "warning",
  "broken": "broken"
}

# Load model
_model = load_model(MODEL_PATH, compile=False)

# Preprocess image
def preprocess_image(image: Image.Image) -> np.ndarray:
  '''
  Function to preprocess the input image for model inference.\n
  params:
  - image: PIL Image object\n
  returns:
  - preprocessed image as numpy array
  '''
  try:
    # Resize image
    img = image.convert("RGB")
    img = img.resize((IMG_W, IMG_H))
    arr = np.asarray(img, dtype=np.float32)
    
    # Ensure correct shape
    if arr.ndim == 2:
      arr = np.stack([arr] * CHANNELS, axis=1)
    
    # Rescale
    arr *= RESCALE
    arr = np.expand_dims(arr, axis=0)  # Add batch dimension
    return arr
  except Exception as e:
    raise CustomException(e, sys)

# Define prediction function
def predict_damage(image: Image.Image) -> Dict[str, Any]:
  '''
  Function to predict damage level from input image.\n
  params:
  - image: PIL Image object\n
  returns:
  - dictionary with prediction results
  '''
  try:
    # Preprocess image
    x = preprocess_image(image)
    
    # Predict
    raw = _model.predict(x)[0]
    raw = raw.astype(float)
    
    # Softmax to get probabilities
    exp = np.exp(raw - np.max(raw))
    probs = exp / exp.sum()
    pred_idx = int(np.argmax(probs))
    pred_label = IDX_TO_LABEL.get(pred_idx, LABELS[pred_idx])
    
    # Get probability for every class
    prob_dict = {
      IDX_TO_LABEL[i]: float(probs[i]) for i in range(len(LABELS))
    }
    
    # Get representative score
    rep_score = float(REP_SCORE_MAP.get(pred_label, 50.0))
    severity_weight = float(SEVERITY_WEIGHTS.get(pred_label, 0.5))
    ui_bucket = _UI_BUCKET_MAP.get(pred_label, pred_label)
    
    return {
      "class": pred_label,
      "ui_bucket": ui_bucket,
      "score": float(probs[pred_idx]),
      "probabilities": prob_dict,
      "rep_score": rep_score,
      "severity_weight": severity_weight,
      "config_version": config.get("version", "unknown"),
      "model_type": config.get("model_type", "unknown")
    }
  except Exception as e:
    raise CustomException(e, sys)