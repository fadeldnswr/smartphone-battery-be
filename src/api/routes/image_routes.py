'''
Routes for image prediction API.
This routes module defines the endpoints for image upload and prediction.
'''

from fastapi import APIRouter, UploadFile, File, HTTPException
from src.api.controller.image_controller import run_image_prediction
from src.api.model.prediction_model import ImagePredictionResponse

# Define router instance
router = APIRouter()

# Define image prediction endpoint
@router.post("/", status_code=200, response_model=ImagePredictionResponse, summary="Upload an image for damage prediction")
async def predict_screen_damage(file: UploadFile = File(..., description="Image file to be uploaded for prediction")) -> ImagePredictionResponse:
  '''
  Endpoint to handle image upload and return damage prediction results.\n
  params:
  - file: Uploaded image file\n
  returns:
  - ImagePredictionResponse containing prediction results
  '''
  try:
    return await run_image_prediction(file)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))