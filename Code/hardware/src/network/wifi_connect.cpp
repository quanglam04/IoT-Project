#include <WiFi.h>       // Thư viện wifi có sẵn trong core của ESP32, build thành công nên không cần để ý đến lỗi
#include "config.h"

void wifi_connect_init() {
    WiFi.mode(WIFI_STA);                        // Đặt ESP32 làm Station mode => thiết bị kết nối vào Wifi có sẵn
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);       // Bắt đầu kết nối đến mạng Wifi đã cấu hình trong config.h
    Serial.print("Connecting WiFi");
    unsigned long start = millis();             // Lưu thời điểm bắt đầu (đếm thời gian từ khi khởi động)

    while (WiFi.status() != WL_CONNECTED) {     // Kiểm tra trạng thái kết nối
        Serial.print(".");
        delay(500);
        if (millis() - start > 20000)   break;  // Sau 20s nếu chưa kết nối được thì break để tránh treo
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected: " + WiFi.localIP().toString());       // Kết nối thành công thì in ra địa chỉ IP mà ESP32 nhận được
    }
    else {
        Serial.println("\nWiFi connect failed");
    }
}

bool wifi_is_connected() {
    return WiFi.status() == WL_CONNECTED;       // Hàm thông báo trạng thái kết nối Wifi
}