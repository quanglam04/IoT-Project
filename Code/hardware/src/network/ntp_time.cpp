// Kết nối đến máy chủ ntp để lấy thời gian thực
// Cập nhật đồng hồ hệ thống trong module ESP

#include <Arduino.h>
#include <time.h>           // Thư viện cho các hàm thao tác thời gian
#include "config.h"         // File cấu hình

// Thiết lập múi giờ offset = 7 * 3600 giây = UTC +7 (giờ Việt Nam/Bangkok)
/*
Thiết lập máy chủ NTP:
+ "pool.ntp.org" (nguồn NTP chung)
+ "time.google.com" (máy chủ thời gian của Google)
*/ 
void ntp_init(){
    configTime(7*3600, 0, "pool.ntp.org","time.google.com");        
    Serial.print("Syncing time");
    int tries = 0;
    while (time(nullptr) < 1600000000 && tries < 20){       // Trả về epoch time với mốc tương ứng với năm 2020. Nếu thời gian hiện tại nhỏ hơn mốc đó => chưa được đồng bộ NTP
    Serial.print(".");
    delay(500);
    tries++;
    }
    Serial.println();
    }

// Trả về thời gian hiện tại dạng epoch, đơn vị là giây
// Dùng để ghi log, hoặc gửi dữ liệu timestamp cho server
time_t get_epoch(){
    return time(nullptr);
}

String iso_now(){
    time_t t = get_epoch();         // Lấy thời gian hiện tại
    struct tm tm;
    gmtime_r(&t, &tm);              // Chuyển từ epoch sang cấu trúc tm ở múi giờ UTC
    char buf[32];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tm);      // Định dạng thời gian thành chuỗi ISO 8601 
    return String(buf);
}
