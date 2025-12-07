#pragma once
#include <Arduino.h>

// ====== CẤU HÌNH PHẦN CỨNG ======
#define PUMP_PIN 23          // GPIO điều khiển Relay hoặc MOSFET
#define RELAY_ACTIVE_HIGH 1  // 1 = HIGH bật, 0 = LOW bật 

// ====== KHAI BÁO HÀM ======
void pump_init();             // Khởi tạo chân I/O
void pump_on();               // Bật bơm
void pump_off();              // Tắt bơm
bool pump_is_on();            // Kiểm tra trạng thái bơm
void pump_toggle();           // Đảo trạng thái bơm
void pump_publish_status();   // Gửi trạng thái bơm lên MQTT
void pump_update();             // Auto stop
void pump_on_with_duration(int duration_min);   // Bật bơm theo duration min