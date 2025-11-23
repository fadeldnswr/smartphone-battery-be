'''
Controller module to handle image prediction requests.
This module defines the ImageController class for processing image uploads
and returning prediction results.
'''

import sys
from io import BytesIO
from typing import Any

from fastapi import UploadFile, File, HTTPException
from PIL import Image

from src.service.image_inference import predict_damage
from src.logging.logging import logging
from src.exception.exception import CustomException
from src.api.model.prediction_model import ImagePredictionResponse

# Define function to run image prediction
async def run_image_prediction(file: UploadFile = File(..., description="Image file to be uploaded for prediction.")) -> ImagePredictionResponse:
  '''
  Function to handle image upload and return prediction results.\n
  params:
  - file: Uploaded image file\n
  returns:
  - ImagePredictionResponse containing prediction results
  '''
  try:
    # Read image file and parse to PIL image
    if file.content_type is None:
      raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image file.")
    
    data = await file.read()
    if not data:
      raise HTTPException(status_code=400, detail="Empty file uploaded. Please provide a valid image file.")
    
    try:
      image = Image.open(BytesIO(data))
    except Exception:
      raise HTTPException(status_code=400, detail="Unable to open image. Please ensure the file is a valid image format.")
    
    logging.info(f"Image file '{file.filename}' received for prediction.")
    
    # Call service inference function
    result: dict[str, Any] = predict_damage(image)
    logging.info(f"Prediction result: {result}")
    
    # Construct response model
    response = ImagePredictionResponse(
      message="Image prediction successful",
      class_label=result.get("class"),
      ui_bucket=result.get("ui_bucket"),
      score=float(result.get("score", 0.0)),
      probabilities={k: float(v) for k, v in result.get("probabilities", {}).items()},
      rep_score=float(result.get("rep_score", 0.0)),
      severity_weight=float(result.get("severity_weight", 0.0)),
      config_version=result.get("config_version"),
      model_type=result.get("model_type"),
    )
    return response
  except HTTPException:
    raise
  except Exception as e:
    logging.error(f"Error in run_image_prediction: {e}")
    raise CustomException(e, sys)