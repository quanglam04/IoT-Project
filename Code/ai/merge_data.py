"""
Script merge data mới với data cũ
Chạy: python merge_data.py
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Files
OLD_FILE = DATA_DIR / "sensor_raw_60d.csv"
NEW_FILE = DATA_DIR / "sensor_live.csv"
OUTPUT_FILE = DATA_DIR / "sensor_combined.csv"

print("=" * 60)
print("🔄 MERGE DATA FILES")
print("=" * 60)

try:
    # Đọc file cũ
    if OLD_FILE.exists():
        df_old = pd.read_csv(OLD_FILE, parse_dates=['ts'])
        print(f"✅ Loaded old data: {len(df_old)} records")
        print(f"   Date range: {df_old['ts'].min()} to {df_old['ts'].max()}")
    else:
        print(f"⚠️  Old file not found: {OLD_FILE}")
        df_old = pd.DataFrame()
    
    # Đọc file mới
    if NEW_FILE.exists():
        df_new = pd.read_csv(NEW_FILE, parse_dates=['ts'])
        print(f"✅ Loaded new data: {len(df_new)} records")
        print(f"   Date range: {df_new['ts'].min()} to {df_new['ts'].max()}")
    else:
        print(f"❌ New file not found: {NEW_FILE}")
        print("   Please run collect_data_mqtt.py first!")
        exit(1)
    
    # Merge
    if not df_old.empty:
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_combined = df_new
    
    # Remove duplicates (based on timestamp + device_id)
    df_combined = df_combined.drop_duplicates(subset=['ts', 'device_id'], keep='last')
    
    # Sort by timestamp
    df_combined = df_combined.sort_values('ts').reset_index(drop=True)
    
    # Save
    df_combined.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n💾 Combined data saved to: {OUTPUT_FILE}")
    print(f"   Total records: {len(df_combined)}")
    print(f"   Date range: {df_combined['ts'].min()} to {df_combined['ts'].max()}")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")

