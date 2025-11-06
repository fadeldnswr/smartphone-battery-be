'''
Usage calculation data models
This module defines data structures for storing and processing application usage statistics.
'''

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Define application usage data model
class AppUsageStats(BaseModel):
  device_id: str
  fg_pkg: str
  total_mb: float
  avg_throughput_mbps: float
  rank: int

# Define application usage response model
class AppUsageResponse(BaseModel):
  device_id: str
  usage_stats: List[AppUsageStats]