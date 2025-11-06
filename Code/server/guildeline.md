[Link docs](https://docs.google.com/document/d/1RxRbX4NSi0xTNWGVxI25GxZe84x3DzggxI1A2Rf8G2Q/edit?usp=sharing)
---

## 1. 📬 MQTT là gì? (Giải thích cho người mới)

Hãy tưởng tượng MQTT giống như một **Tòa soạn báo (Broker)**.

1.  **Broker (Máy chủ trung gian):**
    * Đây là "trái tim" của MQTT. Nó là một phần mềm riêng biệt (ví dụ: Mosquitto, EMQX) mà bạn phải cài đặt và cho nó chạy.
    * Nhiệm vụ của nó là **nhận thư (message) từ bên gửi** và **phát thư (message) cho bên nhận**.

2.  **Publisher (Bên gửi):**
    * Giống như một "Phóng viên".
    * Họ viết một bài báo (gọi là **Payload**, ví dụ: dữ liệu JSON của bạn).
    * Họ gửi bài báo này đến Tòa soạn (Broker) và dán nhãn cho nó, ví dụ: "Gửi cho chuyên mục THỂ THAO" (đây gọi là **Topic**).
    * Phóng viên **không cần biết ai sẽ đọc** bài báo này.

3.  **Subscriber (Bên nhận):**
    * Giống như một "Độc giả".
    * Họ gọi điện cho Tòa soạn (Broker) và nói: "Tôi muốn đăng ký (subscribe) nhận tất cả các bài báo thuộc chuyên mục THỂ THAO".
    * Họ **không cần biết ai đã viết** bài báo đó.
    * Khi nào có bài báo "THỂ THAO" mới, Tòa soạn (Broker) sẽ **tự động đẩy** bài báo đó đến cho Độc giả.

**Kết luận:** Bên gửi (Publisher) và Bên nhận (Subscriber) hoàn toàn **không biết gì về nhau**. Chúng chỉ cần biết địa chỉ của Tòa soạn (Broker) và tên của Chuyên mục (Topic). Đây gọi là "tách rời" (decoupling).

---

## 2. 🤖 Áp dụng MQTT cho Server và AI (Theo file `MQTT.docx`)

Trong dự án của bạn, **cả Server (Node.js) và Model AI đều là "khách hàng" (client)**, chúng cùng kết nối đến **Broker MQTT** mà bạn đã cài đặt.

Luồng giao tiếp bắt buộc (Server <-> AI) sẽ diễn ra làm 2 chiều:

### Chiều 1: Server gửi dữ liệu cho AI (Server ➔ AI)

Mục đích: Server báo cho AI biết "Có dữ liệu cảm biến mới đây, lấy mà train/dự đoán đi".

* **Publisher (Bên gửi):** Server Node.js của bạn.
* **Subscriber (Bên nhận):** Model AI của bạn.
* **Topic (Chủ đề):** Bạn tự định nghĩa, ví dụ: `ai/train/sensordata`.
* **Payload (Nội dung):** Dữ liệu JSON mà ESP32 vừa gửi lên.

**Luồng hoạt động chi tiết:**
1.  ESP32 gửi request `POST /api/sensor` đến Server Node.js (Đây là luồng HTTP, *không phải* MQTT, và nó vẫn đúng).
2.  Hàm `saveSensorData` của bạn được gọi.
3.  Bên trong hàm này, bạn thực hiện `await newData.save()` để lưu vào MongoDB.
4.  **NGAY SAU KHI LƯU XONG**, bạn thêm một đoạn code MQTT (dùng thư viện như `mqtt.js`) để **Publish (Gửi)** dữ liệu `req.body` (chính là JSON cảm biến) lên Topic `ai/train/sensordata`.
5.  Model AI (có thể viết bằng Python) đang **Subscribe (Đăng ký)** Topic `ai/train/sensordata`.
6.  Broker MQTT ngay lập tức **đẩy** dữ liệu JSON này đến cho Model AI. Model AI nhận được và bắt đầu xử lý/dự đoán.

### Chiều 2: AI trả kết quả dự báo về cho Server (AI ➔ Server)

Mục đích: AI báo cho Server "Tôi dự đoán xong rồi, lịch tưới đây, cầm lấy mà lưu".

* **Publisher (Bên gửi):** Model AI của bạn.
* **Subscriber (Bên nhận):** Server Node.js của bạn.
* **Topic (Chủ đề):** Bạn tự định nghĩa, ví dụ: `ai/predict/result`.
* **Payload (Nội dung):** Dữ liệu JSON chứa lịch tưới (action, duration, startTime).

**Luồng hoạt động chi tiết:**
1.  Model AI của bạn chạy dự đoán xong, ra được kết quả là 1 file JSON (ví dụ: `{ "action": "ON", "duration": 300, "startTime": "..." }`).
2.  Model AI dùng thư viện MQTT của nó (ví dụ `paho-mqtt` cho Python) để **Publish (Gửi)** file JSON kết quả này lên Topic `ai/predict/result`.
3.  Server Node.js của bạn (ngoài việc là một Publisher ở chiều 1) **đồng thời cũng là một Subscriber** đang "lắng nghe" Topic `ai/predict/result`.
4.  Broker MQTT ngay lập tức **đẩy** JSON lịch tưới này đến cho Server Node.js.
5.  Server Node.js nhận được JSON này, nó sẽ tạo một bản ghi `Schedule` mới và lưu vào collection `schedules` trong MongoDB.

**Kết quả cuối cùng:** Lịch tưới do AI tạo ra đã nằm an toàn trong CSDL `iot` của bạn. Khi ESP32 gọi `GET /api/schedule/next` (theo file `README.md`), server của bạn chỉ cần vào MongoDB lấy lịch tưới mới nhất (mà AI vừa gửi qua MQTT) ra và trả về cho ESP32.

---

## Luồng AI nhận dữ liệu dễ hiểu

## 1. Quá trình "Đăng ký nhận báo" (Khởi động)

* Khi bạn khởi động chương trình Model AI (viết bằng Python hoặc gì đó), việc đầu tiên nó làm là kết nối đến **Broker MQTT** (Tòa soạn báo).
* Ngay sau khi kết nối thành công, nó gửi một thông điệp đến Broker, nói rằng: "Này Tòa soạn, kể từ giờ, hễ có bài báo nào mới thuộc chủ đề `ai/train/sensordata` thì hãy gửi ngay cho tôi."
* Hành động này gọi là **Subscribe (Đăng ký)**.
* Sau khi đăng ký xong, Model AI không làm gì cả. Nó chỉ ngồi và **"lắng nghe"** (chờ đợi) Tòa soạn báo đưa tin đến.

## 2. Quá trình "Nhận dữ liệu" (Xử lý)

Đây là lúc Server (Node.js) của bạn vào cuộc. Server của bạn là **"Phóng viên" (Publisher)**.

1.  Một cảm biến ESP32 gửi dữ liệu (nhiệt độ, độ ẩm...) đến Server của bạn qua API `POST /api/sensor`.
2.  Server của bạn nhận dữ liệu này, lưu vào cơ sở dữ liệu MongoDB (Kho lưu trữ).
3.  **Ngay sau đó**, Server của bạn (Phóng viên) đóng gói dữ liệu cảm biến đó (Payload) và gửi nó đến **Broker MQTT** (Tòa soạn báo) với nhãn chủ đề (Topic) là `ai/train/sensordata`.
4.  Broker MQTT nhận được tin nhắn này. Nó lập tức kiểm tra xem "Có ai đang đăng ký nhận tin từ `ai/train/sensordata` không?".
5.  Broker thấy "À, có Model AI đang đăng ký!".
6.  Broker **ngay lập tức đẩy (push)** tin nhắn (chứa dữ liệu cảm biến) đó đến cho Model AI của bạn.
7.  Model AI đang "lắng nghe" bỗng nhận được dữ liệu. Nó lấy dữ liệu JSON này làm **đầu vào (input)** và bắt đầu chạy các thuật toán xử lý, dự đoán (ví dụ: mô hình XGBoost của bạn).

---

## 3. 💡 Lợi ích của kiến trúc này

File `MQTT.docx` của bạn đã tóm tắt rất rõ, tôi chỉ nhấn mạnh lại:

* **Tách rời (Decoupling):** Server của bạn không cần biết Model AI chạy ở địa chỉ IP nào. Model AI cũng không cần biết IP của Server. Cả hai chỉ cần biết IP của **Broker MQTT**. Bạn có thể thay đổi, nâng cấp Model AI thoải mái mà không cần sửa code của Server (miễn là nó vẫn subscribe/publish đúng topic).
* **Bất đồng bộ (Asynchronous):** Server gửi dữ liệu cho AI xong là quên luôn (fire-and-forget). Nó không cần phải "chờ" AI xử lý. Khi nào AI xử lý xong, nó sẽ tự động "bắn" kết quả về.
* **Thời gian thực:** Ngay khi AI dự đoán xong, Server sẽ nhận được kết quả ngay lập tức (push) mà không cần phải tốn tài nguyên để liên tục gọi API hỏi AI: "Xong chưa? Xong chưa?".

---

## 4. 📝 Các bước bạn cần làm

1.  **Chọn và Cài đặt Broker:** Đơn giản nhất, bạn hãy cài **Mosquitto** lên cùng máy chủ (hoặc máy tính) đang chạy Server Node.js của bạn.
2.  **Cập nhật Server Node.js:**
    * Cài thư viện: `npm install mqtt`
    * Trong file `index.ts`, bạn khởi tạo 1 MQTT client, kết nối đến Broker và **subscribe** (đăng ký) topic `ai/predict/result`.
    * Viết logic cho "event" khi nhận được message từ topic này: phân tích JSON payload và lưu vào `Schedule.save()`.
    * Trong file `sensor.controller.ts`, sau dòng `await newData.save()`, bạn dùng MQTT client để **publish** (gửi) cái `req.body` đó lên topic `ai/train/sensordata`.
3.  **Cập nhật Model AI:**
    * Cài thư viện MQTT (ví dụ: `pip install paho-mqtt` cho Python).
    * Viết code để **subscribe** (đăng ký) topic `ai/train/sensordata`. Đây sẽ là đầu vào (trigger) để mô hình của bạn chạy.
    * Sau khi có kết quả dự đoán, dùng code để **publish** (gửi) JSON kết quả lên topic `ai/predict/result`.

Tóm lại, toàn bộ kế hoạch đã có sẵn trong file `MQTT.docx` của bạn. Bạn chỉ cần thực hiện theo các bước đó là sẽ hoàn thành yêu cầu.

Bạn có muốn tôi viết một đoạn code mẫu bằng Node.js (dùng `mqtt.js`) để Server của bạn có thể vừa publish vừa subscribe như tôi đã mô tả không?