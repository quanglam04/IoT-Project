// ntp_time.cpp
// Quản lý thời gian NTP, giờ địa phương (GMT+7) và parse ISO8601 chuẩn

#include <Arduino.h>
#include <time.h>
#include "config.h"

// ====================================================
// ===============  NTP INIT (GMT+7)  =================
// ====================================================
void ntp_init() {
    // GMT+7 = 7 * 3600 giây
    configTime(7 * 3600, 0, "pool.ntp.org", "time.google.com");

    Serial.print("⏳ Syncing time");
    int tries = 0;
    while (time(nullptr) < 1600000000 && tries < 20) {
        Serial.print(".");
        delay(500);
        tries++;
    }
    Serial.println();

    if (time(nullptr) > 1600000000)
        Serial.println("✅ Time synced OK (GMT+7)");
    else
        Serial.println("❌ NTP sync failed!");
}

// ====================================================
// ============  GET EPOCH (GIỜ LOCAL)  ===============
// ====================================================
time_t get_epoch() {
    return time(nullptr);  // Đã là giờ GMT+7
}

// ====================================================
// ============  ISO NOW (GIỜ LOCAL)   ================
// ====================================================
String iso_now() {
    time_t t = get_epoch();
    struct tm tm;
    localtime_r(&t, &tm);   // <- GIỜ HÀ NỘI

    char buf[32];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S+07:00", &tm);
    return String(buf);
}

// ====================================================
// =======  Convert epoch → Local ISO (debug)  =========
// ====================================================
String iso_from_epoch(time_t t) {
    struct tm tm;
    localtime_r(&t, &tm);
    char buf[32];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &tm);
    return String(buf);
}

// ====================================================
// ===== PARSE ISO8601 (HỖ TRỢ Z + OFFSET + LOCAL) ====
// ====================================================
//
// Các dạng hỗ trợ:
// - "2025-12-15T07:00:00"
// - "2025-12-15 07:00:00"
// - "2025-12-15T00:00:00Z"
// - "2025-12-15T07:00:00+07:00"
// - "2025-12-15T08:00:00+08:00"
// ====================================================
time_t parseISO8601(const char* s) {
    if (s == nullptr) return 0;

    int year, mon, day, hour, min, sec;
    year = mon = day = hour = min = sec = 0;

    // Parse dạng cơ bản trước
    int parsed = sscanf(s, "%4d-%2d-%2dT%2d:%2d:%2d",
                        &year, &mon, &day, &hour, &min, &sec);

    if (parsed < 6) {
        parsed = sscanf(s, "%4d-%2d-%2d %2d:%2d:%2d",
                        &year, &mon, &day, &hour, &min, &sec);
        if (parsed < 6) return 0;
    }

    // Kiểm tra suffix timezone
    int offsetSign = 0;
    int offsetHour = 0, offsetMin = 0;

    const char* p = strchr(s, 'T');
    if (!p) p = strchr(s, ' ');

    if (p) {
        p += 9; // nhảy qua HH:MM:SS

        if (*p == 'Z') {
            offsetSign = 0; // UTC
        } else if (*p == '+' || *p == '-') {
            offsetSign = (*p == '+') ? 1 : -1;
            sscanf(p + 1, "%2d:%2d", &offsetHour, &offsetMin);
        }
    }

    // Tạo struct tm theo giờ LOCAL
    struct tm tm;
    memset(&tm, 0, sizeof(tm));
    tm.tm_year = year - 1900;
    tm.tm_mon  = mon - 1;
    tm.tm_mday = day;
    tm.tm_hour = hour;
    tm.tm_min  = min;
    tm.tm_sec  = sec;
    tm.tm_isdst = -1;

    time_t local_epoch = mktime(&tm); // xem như local time (GMT+7)

    // Nếu có timezone offset trong string → convert đúng
    if (offsetSign != 0) {
        int totalOffset = offsetSign * (offsetHour * 3600 + offsetMin * 60);

        // Convert từ TIMEZONE về LOCAL GMT+7
        local_epoch -= totalOffset;   // đưa về UTC
        local_epoch += 7 * 3600;      // đưa sang GMT+7
    }

    return local_epoch;
}
