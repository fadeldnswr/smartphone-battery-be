# Battery capacity specifications for different smartphone models (in mAh)
BATTERY_CAPACITY_SPEC = {
  "SM-S931B-57bc0e2d9eac7750": 4090,
  "SM-A556E-7ecd175336df7fc4": 5000,
  "SM-A556E-5f0400c50aae82ca": 5000,
  "V2050-b202c09b34bc8540": 4000,
  "SM-T505-280eb41faa621df0": 7040,
  "SM-A546E-8af17d67f9288898": 5000,
  "SM-A725F-6698366a2e3a4ff1": 5000,
  "2311DRK48G-b135dcd1d7e9320f": 5000,
  "SM-A546E-701861f29b4d5913": 5000,
  "SM-A155F-7d69b63bc200801a": 5000,
  "SM-A336E-c89e0bb491fe3651": 5000,
  "SM-A336E-c471046323c8859c": 5000,
  "Infinix X6886-e495e4491a5c2a82": 5160,
  "SM-A356E-4e32dd36015962aa": 5000,
  "SM-S921B-d2c3f5675ad3a14d": 4000,
  "SM-S926B-1ccc6862dc88e6b9": 4900,
  "Infinix X669C-a1b2d29d54d19af3": 4900,
  "SM-S916B-205d95c2abec51c0": 4700,
  "22021211RG-0940e2943d7b49eb": 4500,
  "SM-A546E-1cf82eec40a3542b": 5000,
  "Redmi Note 9 Pro-d2c7435268ff2367": 5020,
  "24117RN76O-af9a140a5e0ea0de": 5500,
  "2406APNFAG-4b17a6ddf26cd705": 5000,
  "2312DRA50G-223024e791e6150d": 5100,
  "SM-S911B-aee10fcb8586030e": 3900,
}

# Column names in the dataset
TIMESTAMP_COL = "created_at"
DEVICE_COL = "device_id"

# Target columns
SOH_COL = "SoH"
SOH_SMOOTH_COL = "SoH_smooth"
SOH_FILLED_COL = "SoH_filled"
EFC_COL = "EFC"

# Feature columns used for model training
FEATURE_COLS = [
  "batt_voltage_v", "batt_temp_c",
  "throughput_total_mbps", "energy_per_bit_avg_J",
  "EFC", "soh_trend", "efc_delta",
  "temp_ema", "temp_max_win", "tp_ema", "epb_ema",
  "batt_voltage_v_z", "batt_temp_c_z",
  "throughput_total_mbps_z", "energy_per_bit_avg_J_z",
  "SoH_filled_z", "EFC_z", "soh_trend_z", 'BoT_mAh_per_Gbps'
]

WINDOW_SIZE = 24 # Number of time steps in each input sequence
SOH_THRESHOLD_EOL = 0.7 # End-of-life threshold for SoH