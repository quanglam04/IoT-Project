#include <WiFi.h>
#include "config.h"

void wifi_connect_init() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("Connecting WiFi");
    unsigned long start = millis();

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
        if (millis() - start > 20000)   break;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
    }
    else {
        Serial.println("\nWiFi connect failed");
    }
}

bool wifi_is_connected() {
    return WiFi.status() == WL_CONNECTED;
}