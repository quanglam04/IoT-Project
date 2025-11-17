# 🌱 IoT Project – Smart Environment Monitoring & Control

## 📌 Introduction

Dự án IoT này được xây dựng nhằm **giám sát và điều khiển môi trường** (nhiệt độ, độ ẩm, áp suất, mưa, …) thông qua hệ thống cảm biến và bộ điều khiển ESP32.  
Dữ liệu thu thập được sẽ được gửi về server NodeJS/ExpressJS, lưu trữ trên **MongoDB Atlas**, đồng thời hiển thị trực quan trên giao diện web (React + TypeScript).  
Ngoài ra, hệ thống cũng có thể điều khiển **máy bơm, động cơ DC**… theo điều kiện thực tế.

---

## 🛠️ Tech Stack

## Development & Version Control

- **Môi trường phát triển:**
  - PlatformIO
  - Visual Studio Code
- **Quản lý mã nguồn:**
  - Git/Github Server
- **Mạch nguyên lý:**
  - Cirkit Designer

## Backend / Server & Protocol

- **Core:**
  - NodeJS
- **Web Framework:**
  - ExpressJS
- **Ngôn ngữ:**
  - TypeScript
- **Web Protocol:**
  - HTTP
- **Iot Protocol:**
  - MQTT Protocol
- **Real-time:**
  - Socket.io

## Database & Cloud

- **Databse:**
  - MongoDB
  - MongoDB Atlas (Cloud)
- **MQTT Broker:**
  - HiveMQ Cloud

## AI / ML

- **Core Model:**
  - XGBoost

## Hardware & Phần cứng

- **Vi điều khiển:**
  - ESP32(DevKit V1)
- **Cảm biến:**
  - BME280: cảm biến môi trường
  - DHT22: cảm biến nhiệt độ, độ ẩm
- **Thiết bị điều khiển:**
  - Bơm nước mini 12V
- **Module điều khiển:**
  - Module MOSFET
- **Nguồn:**
  - 12V
- **Giao diện người dùng:**
  - ReactJS

## Project Structure

```
IoT/
│
├── Code/
│   ├── ai/                       # Thư mục AI model (train/inference code - Python)
│   │    ├── data/                # Dữ liệu huấn luyện và kiểm thử
│   │    ├── models/              # Model đã train (weights, checkpoints)
│   │    ├── src/                 # Code xử lý dữ liệu, tiền xử lý, inference
│   │    ├── train/               # Script huấn luyện model
│   │    ├── .env                 # Config bí mật (API key, đường dẫn model,…)
│   │    └── requirements.txt     # Thư viện Python cần thiết (TensorFlow, scikit-learn,…)
│   │
│   ├── hardware/                 # Code chạy trên ESP32 (C++ / Arduino)
│   │    ├── control/             # Xử lý điều khiển (bơm nước, quạt, relay,…)
│   │    ├── network/             # Cấu hình & quản lý kết nối Wi-Fi, MQTT, HTTP,...
│   │    ├── sensors/             # Đọc dữ liệu cảm biến (nhiệt độ, độ ẩm, ánh sáng,…)
│   │    ├── utils/               # Hàm tiện ích dùng chung (convert, log, delay,…)
│   │    ├── config.h             # File cấu hình (SSID, password, broker, topic,…)
│   │    └── main.ino             # Chương trình chính của ESP32
│   │
│   ├── server/                   # Backend server (NodeJS + Express)
│   │    ├── config/              # Cấu hình (DB connection, env)
│   │    ├── controllers/         # Xử lý logic cho từng route
│   │    ├── middlewares/         # Xử lý logic cho từng route
│   │    ├── models/              # Định nghĩa schema cho MongoDB
│   │    ├── node_modules/        # Thư viện cài từ npm
│   │    ├── public/              # Static files (CSS, JS, images)
│   │    ├── routes/              # Khai báo các API endpoint + web routes
│   │    ├── sockets/             # Khai báo socket giao tiếp real-time
│   │    ├── services/            # Xử lý logic nghiệp vụ
│   │    ├── templates/           # View engine (EJS templates)
│   │    ├── utils/               # Các hàm tiện ích (gọi AI service, helper)
│   │    ├── shared/              # Code tái sử dụng chung
│   │    │    ├── constants/      # Các hằng số cấu hình, giá trị dùng chung
│   │    │    └── types/          # Định nghĩa kiểu dữ liệu, interface
│   │    ├── .env                 # Config bí mật (DB URI, API key)
│   │    ├── .gitignore           # File loại trừ khi push Git
│   │    ├── index.js             # File chính, khởi tạo Express server
│   │    ├── package.json         # Khai báo dependencies
│   │    └── package-lock.json    # File lock dependencies
│   │
│   └── client/                   # Frontend (React + TypeScript, Vite)
│        ├── public/              # Static assets (favicon, images tĩnh,…)
│        ├── src/                 # Source code chính
│        │   ├── app/             # Core app: layout, pages, styles
│        │   │   ├── layout/      # Layout tổng thể (header, sidebar,…)
│        │   │   ├── pages/       # Các trang chính (Home, Dashboard,…)
│        │   │   ├── styles/      # File CSS/SCSS module
│        │   │   ├── index.tsx    # Entry React app
│        │   │   └── router.tsx   # Định nghĩa router (React Router)
│        │   │
│        │   ├── assets/          # Tài nguyên tĩnh dùng trong app
│        │   │   ├── fonts/       # Font chữ
│        │   │   └── images/      # Hình ảnh
│        │   │
│        │   ├── services/        # Các service gọi API, thao tác Socket
│        │   │
│        │   └── shared/          # Code tái sử dụng chung
│        │       ├── components/  # Component tái sử dụng (button, modal,…)
│        │       ├── constants/   # Các hằng số (API endpoint, config,…)
│        │       ├── context/     # React context (state toàn cục)
│        │       ├── hook/        # Custom hooks
│        │       ├── services/    # Service chung (auth, storage,…)
│        │       ├── types/       # Định nghĩa TypeScript types/interface
│        │       └── utils/       # Hàm tiện ích (format date, string,…)
│        │
│        ├── vite-env.d.ts        # Khai báo env cho Vite + TS
│        ├── .editorconfig        # Quy chuẩn code style
│        ├── .env.development     # Biến môi trường (dev)
│        ├── .env.production      # Biến môi trường (prod)
│        ├── .gitignore           # Loại file không push Git
│        ├── .prettierignore      # Loại file không format
│        ├── .prettierrc          # Config Prettier
│        ├── eslint.config.js     # Config ESLint
│        ├── index.html           # HTML template
│        ├── package.json         # Khai báo dependencies frontend
│        └── package-lock.json    # File lock dependencies frontend
│
├── Documents/                    # Tài liệu báo cáo & slide
│    ├── Báo cáo giữa kỳ.docx
│    ├── Báo cáo cuối kỳ.docx
│    └── slide.txt
│
└── README.md                     # File mô tả dự án

```

---

## 👨‍💻 Team Members

- Trịnh Quang Lâm (Leader)
- Cao Thị Thu Hương
- Vũ Thế Văn
- Vũ Nhân Kiên

---

## System Design

<p align="center">
  <img src="./Code/img/Sơ đồ tổng quan.png" alt="Image title_1" />
</p>
