# API Design

## 1. Sensor (ESP32 ↔ Server)

`POST /api/sensor`

- Mục đích: ESP32 gửi dữ liệu cảm biến môi trường về Server
- Request body

```
{
  "temperature": 28.5,
  "humidity": 65,
  "light": 300,
  "soilMoisture": 40,
  "timestamp": "2025-10-01T10:00:00Z"
}
```

- Server nhận vào request → lưu vào MongoDB (`SensorData`)

`GET /api/schedule/next`

- Mục đích: ESP32 hỏi server để biết lệnh tưới tiếp theo (tự động hoặc thủ công)
- Response Body

```
{
  "action": "ON",
  "duration": 300,      // bơm chạy trong 300 giây
  "startTime": "2025-10-01T11:00:00Z"
}
```

- ESP32 sẽ dựa vào thông tin này để điều khiển bơm/van

## 2. Schedule (User ↔ Server)

`GET /schedule`

- Mục đích: hiển thị toàn bộ lịch tưới hiện tại (AI gen)
- View: render ra giao diện `schedule.ejs`

## 3. Forecast (Server ↔ AI/Weather API)

`GET /forecast`

- Mục đích: hiển thị thông tin dự báo thời tiết / AI forecast trên giao diện web
- View: render `forecast.ejs`

## 4. Dashboard (User ↔ Server)

`GET /dashboard`

- Mục đích: trang chính để user xem dữ liệu tổng quan
- Hiển thị:
  - Dữ liệu sensor mới nhất(temperature, humidity,soil moisture,...)
  - Biểu đổ sensor theo thời gian
  - Forecast ngắn gọn
  - Lịch tưới sắp tới
- View: render `dashboard.ejs`

# Flow

1. ESP32 gửi dữ liệu sensor

- Gửi dữ liệu từ cảm biến qua `POST /api/sensor`. Server nhận, validate -> lưu vào MongoDB (SensorData). Dữ liệu này sau đó được dùng để: Hiển thị biểu đồ trên dashboard, làm input cho AI model dự báo lịch tưới

2. Server gọi AI để dự đoán lịch tưới

- Cron job(đại loại là setup để nó gọi tự động) -> Server gọi `aiService`. `aiService` lấy dữ liệu sensor + thời tiết (qua `api/forecast`)
- AI model chạy inference -> trả về forecast + tưới gợi ý. Server nhận kết quả -> lưu vào DB (Forecast, Schedule)

3. ESP32 lấy lịch tưới
4. User xem & thao tác trên web

- /dashboard: user thấy biểu đố sensor + forecast + lịch tưới
- /forecast: xem thông tin dự báo
