'''
Main file for smartphone battery health prediction thesis project
'''
import sys, os

from fastapi import FastAPI
from typing import Dict, Any
from src.exception.exception import CustomException

# Define instances
app = FastAPI(
  title="Smartphone Battery Health Prediction API",
  description="API for predicting smartphone battery health using machine learning models",
  version="1.0.0"
)

# Create welcome page route
@app.get("/")
async def welcome_page() -> Dict[str, Any]:
  try:
    return {
      "message":"Welcome to the Smartphone Battery Health Prediction API",
    }
  except Exception as e:
    raise CustomException(e, sys)