"""
Script lấy dữ liệu lịch sử từ OpenWeatherMap API để train model.

Chạy: python src/fetch_owm_data.py

Lưu ý:
- OpenWeatherMap History API chỉ có trong subscription (paid)
- Free tier chỉ có Current Weather + Forecast
- Nếu không có History API, ta sẽ dùng Forecast API và lưu lại để làm "pseudo history"
"""

import os
import json
import time
import math
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# ====== CẤU HÌNH ======
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

OWM_API_KEY = "3cb2d08dd66ccc2cfe23b91939d437af"
LATITUDE = 21.0245
LONGITUDE = 105.8412

OUTPUT_FILE = DATA_DIR / "owm_history.csv"

# ====== OpenWeatherMap API Endpoints ======
# Current Weather API (free tier)
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
# One Call API 3.0 (cần subscription)
ONECALL_URL_3 = "https://api.openweathermap.org/data/3.0/onecall"
# One Call API 2.5 (deprecated nhưng vẫn hoạt động, free tier)
ONECALL_URL_25 = "https://api.openweathermap.org/data/2.5/onecall"
# Historical Weather Data API (cần subscription, chỉ 5 ngày gần nhất)
HISTORICAL_URL = "https://api.openweathermap.org/data/2.5/onecall/timemachine"


def fetch_current_weather() -> Optional[Dict]:
    """Lấy dữ liệu thời tiết hiện tại."""
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "vi"
    }
    
    try:
        response = requests.get(CURRENT_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching current weather: {e}")
        return None


def fetch_onecall_forecast() -> Optional[Dict]:
    """Lấy dữ liệu One Call API (current + hourly forecast 48h)."""
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "vi",
        "exclude": "minutely,daily,alerts"  # Chỉ lấy current + hourly
    }
    
    # Thử One Call API 2.5 trước (free tier)
    try:
        response = requests.get(ONECALL_URL_25, params=params, timeout=10)
        response.raise_for_status()
        print(f"   ✓ Using One Call API 2.5")
        return response.json()
    except Exception as e:
        print(f"   ⚠️  One Call API 2.5 failed: {e}")
    
    # Thử One Call API 3.0 (cần subscription)
    try:
        response = requests.get(ONECALL_URL_3, params=params, timeout=10)
        response.raise_for_status()
        print(f"   ✓ Using One Call API 3.0")
        return response.json()
    except Exception as e:
        print(f"   ⚠️  One Call API 3.0 failed: {e}")
        return None


def parse_weather_data(data: Dict, timestamp: datetime) -> Dict:
    """
    Parse dữ liệu từ OpenWeatherMap API thành format chuẩn.
    
    Input: JSON từ API
    Output: Dict với các field cần thiết cho training
    """
    result = {
        "ts": timestamp.isoformat(),
        "api_temp_c": data.get("main", {}).get("temp", 0.0),
        "api_rh_pct": data.get("main", {}).get("humidity", 0.0),
        "api_pressure_hpa": data.get("main", {}).get("pressure", 0.0),
        "api_uvi": data.get("uvi", 0.0),  # Có thể không có trong current weather
        "api_wind_speed": data.get("wind", {}).get("speed", 0.0),
        "api_cloud_pct": data.get("clouds", {}).get("all", 0.0),
        "api_weather_code": data.get("weather", [{}])[0].get("id", 0),
        "api_weather_main": data.get("weather", [{}])[0].get("main", ""),
        "api_weather_desc": data.get("weather", [{}])[0].get("description", ""),
    }
    
    # Tính dew point từ temp và humidity
    temp = result["api_temp_c"]
    rh = result["api_rh_pct"]
    if temp > 0 and rh > 0:
        a, b = 17.27, 237.7
        gamma = (a * temp / (b + temp)) + math.log(max(rh, 1e-3) / 100.0)
        result["api_dew_point"] = (b * gamma) / (a - gamma)
    else:
        result["api_dew_point"] = 0.0
    
    # Rain data (có thể không có)
    rain_1h = data.get("rain", {}).get("1h", 0.0)
    result["api_rain_1h"] = rain_1h
    
    # Probability of precipitation (POP) - không có trong current weather
    # Sẽ lấy từ forecast API
    result["api_pop"] = 0.0
    
    return result


def parse_onecall_hourly(hourly_data: List[Dict], base_time: datetime) -> List[Dict]:
    """
    Parse hourly forecast từ One Call API.
    
    hourly_data: List các dict từ API (48 giờ tới)
    """
    results = []
    
    for item in hourly_data:
        dt = datetime.fromtimestamp(item["dt"], tz=None)
        
        # Tính dew point
        temp = item.get("temp", 0.0)
        rh = item.get("humidity", 0.0)
        if temp > 0 and rh > 0:
            a, b = 17.27, 237.7
            gamma = (a * temp / (b + temp)) + math.log(max(rh, 1e-3) / 100.0)
            dew_point = (b * gamma) / (a - gamma)
        else:
            dew_point = 0.0
        
        result = {
            "ts": dt.isoformat(),
            "api_temp_c": temp,
            "api_rh_pct": rh,
            "api_pressure_hpa": item.get("pressure", 0.0),
            "api_uvi": item.get("uvi", 0.0),
            "api_wind_speed": item.get("wind_speed", 0.0),
            "api_cloud_pct": item.get("clouds", 0.0),
            "api_weather_code": item.get("weather", [{}])[0].get("id", 0),
            "api_weather_main": item.get("weather", [{}])[0].get("main", ""),
            "api_weather_desc": item.get("weather", [{}])[0].get("description", ""),
            "api_dew_point": dew_point,
            "api_rain_1h": item.get("rain", {}).get("1h", 0.0),
            "api_pop": item.get("pop", 0.0),  # Probability of precipitation
        }
        results.append(result)
    
    return results


def fetch_and_save_history(days_back: int = 60) -> None:
    """
    Lấy dữ liệu lịch sử từ API.
    
    Lưu ý: OpenWeatherMap History API cần subscription.
    Nếu không có, ta sẽ:
    1. Lấy forecast hiện tại (48h)
    2. Lưu lại để dùng làm "pseudo history" cho training
    """
    print(f"📡 Fetching OpenWeatherMap data for {LATITUDE}, {LONGITUDE}...")
    print(f"   API Key: {OWM_API_KEY[:10]}...")
    
    all_data = []
    
    # Option 1: Thử lấy One Call API (có hourly forecast 48h)
    print("\n1️⃣ Fetching One Call API (current + 48h forecast)...")
    onecall_data = fetch_onecall_forecast()
    
    if onecall_data:
        # Parse current weather
        if "current" in onecall_data:
            current = onecall_data["current"]
            dt = datetime.fromtimestamp(current["dt"], tz=None)
            parsed = parse_weather_data(current, dt)
            # Thêm pop từ forecast nếu có
            if "hourly" in onecall_data and len(onecall_data["hourly"]) > 0:
                parsed["api_pop"] = onecall_data["hourly"][0].get("pop", 0.0)
            all_data.append(parsed)
            print(f"   ✓ Current weather: {dt}")
        
        # Parse hourly forecast
        if "hourly" in onecall_data:
            hourly = parse_onecall_hourly(onecall_data["hourly"], datetime.now())
            all_data.extend(hourly)
            print(f"   ✓ Hourly forecast: {len(hourly)} hours")
    
    # Option 2: Nếu One Call không có, dùng Current Weather API
    if not all_data:
        print("\n2️⃣ Fallback: Fetching Current Weather API...")
        current_data = fetch_current_weather()
        if current_data:
            parsed = parse_weather_data(current_data, datetime.now())
            all_data.append(parsed)
            print(f"   ✓ Current weather saved")
    
    # Lưu vào CSV
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values("ts").reset_index(drop=True)
        
        # Nếu file đã tồn tại, merge với dữ liệu cũ
        if OUTPUT_FILE.exists():
            df_old = pd.read_csv(OUTPUT_FILE, parse_dates=["ts"])
            df_combined = pd.concat([df_old, df], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=["ts"], keep="last")
            df_combined = df_combined.sort_values("ts").reset_index(drop=True)
            df = df_combined
        
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Saved {len(df)} records to {OUTPUT_FILE}")
        print(f"   Time range: {df['ts'].min()} → {df['ts'].max()}")
    else:
        print("\n❌ No data fetched. Check API key and network connection.")
    
    # Hiển thị sample
    if len(all_data) > 0:
        print("\n📊 Sample data:")
        print(df.head().to_string())


def main():
    """Main function."""
    print("=" * 70)
    print("🌤️  OpenWeatherMap Data Fetcher")
    print("=" * 70)
    
    # Lấy dữ liệu
    fetch_and_save_history(days_back=60)
    
    print("\n" + "=" * 70)
    print("💡 Note: OpenWeatherMap History API requires subscription.")
    print("   This script fetches current + forecast data as 'pseudo history'.")
    print("   For real historical data, consider using OpenWeatherMap History API")
    print("   or download bulk historical data from their website.")
    print("=" * 70)


if __name__ == "__main__":
    main()

