'''
Routes for impact calculation endpoints.
This module defines the API routes for calculating e-waste impact based on device parameters.
'''

from fastapi import APIRouter, HTTPException
from src.api.controller.recommendation_controller import run_impact_calculation
from src.api.model.impact_model import ImpactRequest, ImpactResponse

# Define router instances
router = APIRouter()

# Define route for impact calculation
@router.post("/carbon-ewaste", response_model=ImpactResponse, summary="Calculate e-waste and carbon impact based on device parameters.")
async def compute_carbon_ewaste_impact(payload: ImpactRequest) -> ImpactResponse:
  try:
    return run_impact_calculation(payload)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))