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

# Define battery cost of traffic point
class BatteryCostOfTrafficPoint(BaseModel):
  timestamp: datetime
  bot_mAh_per_Gbps: float

# Define energy per bit point
class EnergyPerBitPoint(BaseModel):
  timestamp: datetime
  energy_per_bit_tx_J: float
  energy_per_bit_rx_J: float
  energy_per_bit_avg_J: float

# Define throughput history model
class GraphsHistoryResponse(BaseModel):
  message: str
  device_id: str
  thr_points: List[ThroughputPoint]
  energy_points: List[EnergyConsumptionPoint]
  energy_per_bit_points: List[EnergyPerBitPoint]
  bot_points: List[BatteryCostOfTrafficPoint]