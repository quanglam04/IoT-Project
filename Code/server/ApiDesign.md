# API Design (Đã chuyển sang MQTT)

Kiến trúc này sử dụng một **MQTT Broker** trung gian. Tất cả các thành phần (ESP32, Server, AI, Web UI) đều là "client" kết nối đến Broker này.

## 1. Luồng Cảm biến (ESP32 ➔ Server ➔ AI)

### Topic: `sensor/data/push`

* **Publisher (Bên gửi):** **ESP32**
* **Subscriber (Bên nhận):** **Server Node.js**
* **Mục đích:** ESP32 gửi dữ liệu cảm biến môi trường về Server.
* **Payload (Nội dung tin nhắn):**

    ```json
    {
      "temperature": 28.5,
      "humidity": 65,
      "light": 300,
      "soilMoisture": 40,
      "timestamp": "2025-10-01T10:00:00Z"
    }
    ```

* **Hoạt động:** Server "lắng nghe" (subscribe) topic này. Khi nhận được tin nhắn, Server sẽ:
    1.  Lưu vào MongoDB (`SensorData`).
    2.  Publish tin nhắn này lên `ai/train/input` để AI xử lý.
    3.  Publish tin nhắn này lên `dashboard/update/sensor` để Web UI cập nhật.

## 2. Luồng Giao tiếp Server ↔ AI (Bắt buộc qua MQTT)

### Topic: `ai/train/input`

* **Publisher (Bên gửi):** **Server Node.js**
* **Subscriber (Bên nhận):** **Model AI**
* **Mục đích:** Server chuyển tiếp dữ liệu cảm biến (ngay khi nhận từ ESP32) cho AI làm đầu vào.
* **Payload:** Giống hệt payload của `sensor/data/push`.

### Topic: `ai/predict/result`

* **Publisher (Bên gửi):** **Model AI**
* **Subscriber (Bên nhận):** **Server Node.js**
* **Mục đích:** Model AI gửi trả kết quả dự báo (lịch tưới gợi ý) về cho Server.
* **Payload:**

    ```json
    {
      "action": "ON",
      "duration": 300,
      "startTime": "2025-10-01T11:00:00Z"
    }
    ```

* **Hoạt động:** Server "lắng nghe" (subscribe) topic này. Khi nhận được kết quả, Server sẽ:
    1.  Lưu vào MongoDB (`Schedule`).
    2.  Publish lệnh này lên `device/control/schedule` để ESP32 thực thi.
    3.  Publish lệnh này lên `dashboard/update/schedule` để Web UI cập nhật.

## 3. Luồng Điều khiển (Server ➔ ESP32)

### Topic: `device/control/schedule`

* **Publisher (Bên gửi):** **Server Node.js**
* **Subscriber (Bên nhận):** **ESP32**
* **Mục đích:** Server gửi lệnh tưới (từ AI hoặc thủ công) xuống cho ESP32.
* **Payload:**

    ```json
    {
      "action": "ON",
      "duration": 300,      // bơm chạy trong 300 giây
      "startTime": "2025-10-01T11:00:00Z"
    }
    ```

* **Hoạt động:** ESP32 "lắng nghe" (subscribe) topic này. Khi nhận được lệnh, nó sẽ thực thi (ví dụ: bật bơm trong 300 giây).

## 4. Luồng Dashboard (Server ➔ User/Web UI)

Thay vì Web UI gọi `GET` để lấy dữ liệu, Server sẽ chủ động *đẩy* dữ liệu lên các topic mà Web UI "lắng nghe".

### Topic: `dashboard/update/sensor`

* **Publisher (Bên gửi):** **Server Node.js**
* **Subscriber (Bên nhận):** **Web UI (React App)**
* **Mục đích:** Cập nhật dữ liệu sensor mới nhất lên biểu đồ.
* **Payload:** Giống payload của `sensor/data/push`.

### Topic: `dashboard/update/schedule`

* **Publisher (Bên gửi):** **Server Node.js**
* **Subscriber (Bên nhận):** **Web UI (React App)**
* **Mục đích:** Cập nhật lịch tưới (từ AI) lên giao diện.
* **Payload:** Giống payload của `ai/predict/result`.

### Topic: `dashboard/update/forecast`

* **Publisher (Bên gửi):** **Server Node.js** (sau khi gọi API thời tiết hoặc AI xử lý)
* **Subscriber (Bên nhận):** **Web UI (React App)**
* **Mục đích:** Cập nhật thông tin dự báo thời tiết.
* **Payload (Ví dụ):**
    ```json
    {
      "chanceOfRain": 80,
      "recommendation": "Trời sắp mưa, không cần tưới"
    }
    ```

---

# Flow (Đã cập nhật theo MQTT)

1.  **ESP32 gửi dữ liệu sensor:**
    * ESP32 **Publish** dữ liệu (JSON) lên topic `sensor/data/push`.

2.  **Server xử lý dữ liệu và yêu cầu AI dự đoán:**
    * Server (đang **Subscribe** `sensor/data/push`) nhận được dữ liệu.
    * Server lưu dữ liệu vào MongoDB (`SensorData`).
    * Server **Publish** ngay dữ liệu này sang topic `ai/train/input` (cho AI).
    * Server **Publish** ngay dữ liệu này sang topic `dashboard/update/sensor` (cho Web UI).

3.  **AI dự đoán và trả kết quả:**
    * Model AI (đang **Subscribe** `ai/train/input`) nhận được dữ liệu và chạy dự đoán.
    * AI **Publish** kết quả (lịch tưới JSON) lên topic `ai/predict/result`.

4.  **Server nhận kết quả AI và điều khiển/cập nhật:**
    * Server (đang **Subscribe** `ai/predict/result`) nhận được lịch tưới từ AI.
    * Server lưu lịch tưới này vào MongoDB (`Schedule`).
    * Server **Publish** lịch tưới này lên topic `device/control/schedule` (cho ESP32).
    * Server **Publish** lịch tưới này lên topic `dashboard/update/schedule` (cho Web UI).

5.  **Thiết bị và Người dùng nhận cập nhật (đồng thời):**
    * **ESP32** (đang **Subscribe** `device/control/schedule`) nhận lệnh và bật/tắt bơm.
    * **Web UI** (đang **Subscribe** `dashboard/update/sensor` và `dashboard/update/schedule`) nhận dữ liệu mới và cập nhật giao diện (biểu đồ, trạng thái) ngay lập tức.