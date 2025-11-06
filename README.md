# 🌱 IoT Project – Smart Environment Monitoring & Control

## 📌 Introduction

Dự án IoT này được xây dựng nhằm **giám sát và điều khiển môi trường** (nhiệt độ, độ ẩm, áp suất, mưa, …) thông qua hệ thống cảm biến và bộ điều khiển ESP32.  
Dữ liệu thu thập được sẽ được gửi về server NodeJS/ExpressJS, lưu trữ trên **MongoDB Atlas**, đồng thời hiển thị trực quan trên giao diện web (React + TypeScript).  
Ngoài ra, hệ thống cũng có thể điều khiển **máy bơm, động cơ DC**… theo điều kiện thực tế.

---

## 🛠️ Tech Stack

### Development Tools

- **Arduino IDE**
- **Visual Studio Code**

### Backend / Server

- **NodeJS (22.17.1)**
- **ExpressJS**
- **Web Service**: HTTP

### Database & Cloud

- **MongoDB**
- **MongoDB Atlas**

### AI / ML

- **TensorFlow.js** (inference trên Node: `@tensorflow/tfjs-node`)
- (Tùy chọn) **TensorFlow (Python)** hoặc **PyTorch** để huấn luyện offline và convert model sang TF.js format.

### Hardware

- **Vi điều khiển:** ESP32
- **Cảm biến:**
  - SHT30 (nhiệt độ, độ ẩm)
  - BMP280, BME280 (áp suất không khí, nhiệt độ, độ ẩm)
  - Cảm biến mưa
- **Thiết bị điều khiển:**
  - Nguồn 12V
  - Module bơm
  - Động cơ DC 1 chiều
  - Linh kiện vỏ, phụ kiện khác
- **Mạch nguyên lý:** Proteus 8

## Project Structure

```
IoT/
│
├── Code/
│   ├── ai/                       # Thư mục AI model (train/inference code)
│   │    └── ...
│   │
│   ├── hardware/                 # Code chạy trên ESP32 (C++)
│   │    └── example.cpp          # Ví dụ code kết nối & gửi dữ liệu
│   │
│   ├── server/                   # Backend server (NodeJS + Express)
│   │    ├── config/              # Cấu hình (DB connection, env)
│   │    ├── controllers/         # Xử lý logic cho từng route
│   │    ├── models/              # Định nghĩa schema cho MongoDB
│   │    ├── node_modules/        # Thư viện cài từ npm
│   │    ├── public/              # Static files (CSS, JS, images)
│   │    ├── routes/              # Khai báo các API endpoint + web routes
│   │    ├── templates/           # View engine (EJS templates)
│   │    ├── utils/               # Các hàm tiện ích (gọi AI service, helper)
│   │    ├── .env                 # Config bí mật (DB URI, API key)
│   │    ├── .gitignore           # File loại trừ khi push Git
│   │    ├── index.js             # File chính, khởi tạo Express server
│   │    ├── package.json         # Khai báo dependencies
│   │    └── package-lock.json
│   └──client/                    # Frontend (React + TypeScript, Vite)
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
│        │   ├── services/        # Các service gọi API
│        │   │   └── client.service.ts  # Hàm call API client
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
├── Documents/               # Tài liệu báo cáo & slide
│    ├── Báo cáo cuối kỳ.docx
│    ├── Báo cáo giữa kỳ.docx
│    └── slide.txt
│
└── README.md                # File mô tả dự án
```

---

## 👨‍💻 Team Members

- Trịnh Quang Lâm
- Cao Thị Thu Hương
- Vũ Thế Văn
- Vũ Nhân Kiên

---
