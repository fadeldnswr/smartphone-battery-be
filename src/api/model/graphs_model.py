'''
Graphs visualization models
This module defines the data models used for graph visualization based on throughput metrics.
'''
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Define throughput point
class ThroughputPoint(BaseModel):
  timestamp: datetime
  throughput_total_mbps: float
  throughput_upload_mbps: float
  throughput_download_mbps: float

# Define energy consumption point
class EnergyConsumptionPoint(BaseModel):
  timestamp: datetime
  energy_wh: float

# Define throughput history model
class GraphsHistoryResponse(BaseModel):
  message: str
  device_id: str
  thr_points: List[ThroughputPoint]
  thr_energy: List[EnergyConsumptionPoint]
