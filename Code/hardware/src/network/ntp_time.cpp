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

// parse ISO8601 basic without timezone suffix: "2025-12-10T07:00:00" or "2025-12-10T07:00:00Z"
// Assumes local time (configTime was called earlier). Returns time_t (seconds since epoch).
time_t parseISO8601(const char* iso8601) {
    if (iso8601 == nullptr) return 0;
    int year=0, mon=0, day=0, hour=0, min=0, sec=0;
    // support both with and without trailing 'Z'
    // formats: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS
    if (sscanf(iso8601, "%4d-%2d-%2dT%2d:%2d:%2d", &year, &mon, &day, &hour, &min, &sec) < 6) {
        if (sscanf(iso8601, "%4d-%2d-%2d %2d:%2d:%2d", &year, &mon, &day, &hour, &min, &sec) < 6) {
            return 0;
        }
    }
    struct tm tm;
    memset(&tm, 0, sizeof(tm));
    tm.tm_year = year - 1900;
    tm.tm_mon  = mon - 1;
    tm.tm_mday = day;
    tm.tm_hour = hour;
    tm.tm_min  = min;
    tm.tm_sec  = sec;
    tm.tm_isdst = -1;
    // mktime treats tm as local time; configTime should already set TZ
    time_t t = mktime(&tm);
    return t;
}
