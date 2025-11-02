'''
Raw metrics data model.
This module defines the RawMetrics class for handling raw metrics data.
'''
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Define RawMetrics data model
class RawMetrics(BaseModel):
  user_id: Optional[str] = None
  device_id: str
  channel_quality: float
  ts_uts: datetime
  net_type: str
  rx_total_bytes: int
  tx_total_bytes: int
  batt_voltage_mv: int
  batt_current_ua: int
  fg_pkg: str
  batt_temp_c: float
  is_charging: bool
  charge_source: str
  battery_health: str
  cycles_count: Optional[int] = None
  battery_level: int
  charge_counter_uah: int
  energy_nwh: Optional[int] = None
  battery_capacity_pct: int
  current_avg_ua: Optional[int] = None

# Define metrics response model
class RawMetricsResponse(BaseModel):
  message: str
  data: List[Dict[str, Any]]