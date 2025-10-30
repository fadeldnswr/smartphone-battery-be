"""
Main file for smartphone battery health prediction thesis project
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from typing import Dict
from src.api.routes import data_retrieval

# Define instances
app = FastAPI(
    title="Smartphone Battery Health Prediction API",
    description="API for collecting and visualizing smartphone battery health data.",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define routes
app.include_router(data_retrieval.router, prefix="/data-retrieval", tags=["Data Retrieval"])

# Define root endpoint
@app.get("/", status_code=200)
async def root() -> Dict[str, str]:
    """
    Root endpoint to verify API is running.
    """
    return {"message": "Smartphone Battery Health Prediction API is running."}