'''
Data models for battery health metrics.
This module defines data structures for storing and processing battery health metrics.
'''
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Define battery metrics data model
class StateOfHealth(BaseModel):
  device_id: str
  created_at: datetime
  Q_mAh: float
  Ct_mAh: float
  soh_pct: float

# Define battery cycles data model
class BatteryCycles(BaseModel):
  device_id: str
  created_at: datetime
  delta_charge_uah: float
  discharge_uah: float
  cycles_est: float

# Define battery metrics response model
class BatteryMetricsResponse(BaseModel):
  device_id: str
  soh_data: List[StateOfHealth]
  cycles_data: List[BatteryCycles]