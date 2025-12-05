#include "fota_update.h"
#include "config.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Update.h>

#include "../network/mqtt_client.h"  

// MAX redirect hops để tránh vòng lặp vô hạn
#define MAX_REDIRECTS 3
// Kích thước buffer đọc từ HTTP stream
#define READ_BUFFER_SIZE 1024
// Báo progress khi tăng >= PROGRESS_STEP %
#define PROGRESS_STEP 5
// Khoảng thời gian gọi mqtt_loop() trong vòng đọc (ms)
#define MQTT_LOOP_YIELD_MS 1
// Thời gian tối đa chờ download (ms) - phòng trường hợp treo
#define DOWNLOAD_TIMEOUT_MS (5 * 60 * 1000) // 5 phút

bool fota_update(String url) {
    Serial.println("\n==============================");
    Serial.println("🚀 FOTA UPDATE START (HTTPS)");
    Serial.println("==============================");
    Serial.printf("📡 Start URL: %s\n", url.c_str());

    // Thông báo bắt đầu
    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"starting\"}");

    WiFiClientSecure client;
    client.setInsecure(); // nếu bạn có CA hợp lệ -> setCACert(...)

    HTTPClient http;
    String currentUrl = url;
    int redirectCount = 0;
    int httpCode = -1;

    // Theo dõi thời gian bắt đầu để có timeout tổng
    unsigned long tStartTotal = millis();

    // ---------- Xử lý redirect đơn giản (theo Location header) ----------
    while (redirectCount <= MAX_REDIRECTS) {
        if (!http.begin(client, currentUrl)) {
            Serial.println("❌ ERROR: http.begin() thất bại!");
            mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"begin\"}");
            return false;
        }

        httpCode = http.GET();

        // Nếu redirect (301/302/307...), lấy header Location và lặp lại
        if (httpCode == HTTP_CODE_MOVED_PERMANENTLY ||
            httpCode == HTTP_CODE_FOUND ||
            httpCode == HTTP_CODE_SEE_OTHER ||
            httpCode == HTTP_CODE_TEMPORARY_REDIRECT ||
            httpCode == 308) {
            String newLocation = http.header("Location");
            Serial.printf("➡ Redirect %d -> %s\n", redirectCount, newLocation.c_str());
            http.end();
            if (newLocation.length() == 0) {
                Serial.println("❌ Redirect nhưng không có Location header!");
                mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"redirect_no_location\"}");
                return false;
            }
            currentUrl = newLocation;
            redirectCount++;
            continue;
        }

        break;
    }

    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("❌ HTTP GET FAILED: %d\n", httpCode);
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"download\"}");
        http.end();
        return false;
    }

    int total = http.getSize();
    if (total <= 0) {
        Serial.println("❌ ERROR: File OTA rỗng hoặc không đúng!");
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"invalid_file\"}");
        http.end();
        return false;
    }

    // Báo bắt đầu download
    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"downloading\",\"size\":" + String(total) + "}");
    Serial.printf("📥 File size: %d bytes\n", total);

    WiFiClient *stream = http.getStreamPtr();

    // Chuẩn bị flash
    if (!Update.begin((size_t)total)) {
        Serial.printf("❌ Update.begin() ERROR: %s\n", Update.errorString());
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"flash_begin\"}");
        http.end();
        return false;
    }

    // Đọc theo chunk và ghi vào flash
    uint8_t buffer[READ_BUFFER_SIZE];
    size_t written = 0;
    int lastProgress = -1;
    unsigned long tStart = millis();

    while (written < (size_t)total) {
        // Timeout tổng trong khi download
        if (millis() - tStartTotal > DOWNLOAD_TIMEOUT_MS) {
            Serial.println("❌ ERROR: Download timeout");
            mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"download_timeout\"}");
            Update.abort();
            http.end();
            return false;
        }

        // Nếu stream không có data, chờ 1ms, đồng thời giữ MQTT alive
        if (!stream->available()) {
            // Thả CPU ngắn, gọi loop MQTT để giữ kết nối
            mqtt_loop();
            delay(MQTT_LOOP_YIELD_MS);
            continue;
        }

        int toRead = stream->available();
        if (toRead > READ_BUFFER_SIZE) toRead = READ_BUFFER_SIZE;
        int r = stream->readBytes(buffer, toRead);
        if (r <= 0) {
            // Nếu read lỗi, thoát
            Serial.println("❌ ERROR: readBytes returned <= 0");
            mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"read_failed\"}");
            Update.abort();
            http.end();
            return false;
        }

        // Ghi phần vừa đọc vào flash
        size_t w = Update.write(buffer, (size_t)r);
        if (w != (size_t)r) {
            Serial.printf("❌ ERROR: Update.write returned %u expected %d\n", (unsigned)w, r);
            mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"flash_write\"}");
            Update.abort();
            http.end();
            return false;
        }

        written += w;

        // Tính progress và publish mỗi PROGRESS_STEP %
        int progress = (int)((written * 100) / total);
        if (progress - lastProgress >= PROGRESS_STEP || written == (size_t)total) {
            lastProgress = progress;
            String pmsg = String("{\"status\":\"writing\",\"progress\":") + String(progress) +
                          String(",\"written\":") + String(written) +
                          String(",\"total\":") + String(total) + String("}");
            mqtt_publish(TOPIC_UPDATE_STATUS, pmsg);
            // Gọi mqtt_loop ngắn để giữ MQTT gửi kịp, không block lâu
            mqtt_loop();
        }

        // Nếu quá lâu giữa các read, break (safety)
        if (millis() - tStart > DOWNLOAD_TIMEOUT_MS) {
            Serial.println("❌ ERROR: Per-download timeout");
            mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"download_timeout\"}");
            Update.abort();
            http.end();
            return false;
        }
    }

    Serial.printf("✅ Downloaded %u bytes, finalizing...\n", (unsigned)written);

    // Kết thúc update
    if (!Update.end()) {
        Serial.printf("❌ OTA ERROR: %s\n", Update.errorString());
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"flash_end\"}");
        http.end();
        return false;
    }

    // Kiểm tra CRC/MD5 nếu cần (Update.hasError() check)
    if (Update.isFinished() == false) {
        Serial.println("❌ OTA NOT finished?");
        mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"error\",\"step\":\"not_finished\"}");
        http.end();
        return false;
    }

    http.end();

    // Gửi "done"
    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"done\",\"written\":" + String(written) + "}");

    // Flush MQTT & TLS: đảm bảo broker nhận message
    // mqtt_flush() đã được implement ở mqtt_client.cpp — gọi nó
    mqtt_flush(2500);

    // Thêm 1 message "rebooting" để broker chắc chắn biết
    mqtt_publish(TOPIC_UPDATE_STATUS, "{\"status\":\"rebooting\"}");
    mqtt_flush(1500);

    Serial.println("🔁 Restarting now...");
    delay(500);
    ESP.restart();

    // unreachable
    return true;
}
