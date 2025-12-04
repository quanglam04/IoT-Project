#pragma once
#include <Arduino.h>

/**
 * Hàm cập nhật firmware OTA từ URL
 * Trả về true nếu thành công
 */
bool fota_update(String url);
