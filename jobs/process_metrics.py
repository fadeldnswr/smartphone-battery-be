#!/usr/bin/env python3
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Load Supabase credentials
load_dotenv("/home/ubuntu/smartphone-battery-be/.env")

SUPABASE_URL = os.getenv("SUPABASE_API_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")  # gunakan service key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    now = datetime.now(timezone.utc)
    five_min_ago = now - timedelta(minutes=5)

    print(f"[{now.isoformat()}] Running 5-minute job...")

    # Ambil data 5 menit terakhir dari raw_metrics
    data = (
        supabase.table("raw_metrics")
        .select("*")
        .gte("ts_utc", five_min_ago.isoformat())
        .execute()
    ).data or []

    if not data:
        print("❗ No data found in last 5 minutes.")
        return

    print(f"✅ Found {len(data)} new rows")

    # Contoh agregasi sederhana per device
    for row in data:
        supabase.table("metrics_5min").insert({
            "device_id": row["device_id"],
            "ts_bucket": now.isoformat(),
            "battery_level": row.get("battery_level"),
            "net_type": row.get("net_type"),
            "rssi": row.get("channel_quality"),
            "is_charging": row.get("is_charging"),
        }).execute()

    print("✅ Metrics processed and inserted successfully.")

if __name__ == "__main__":
    main()
