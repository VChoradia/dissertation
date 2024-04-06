#ifndef WIFI_CONTROL_H
#define WIFI_CONTROL_H

#include <WiFi.h>

// network credentials
const char* ssid = "uos-other";
const char* password = "shefotherkey05";

// Adapted from COM 3505 Internet of Things Weekly Lab Solutions authored by Prof. Hamish Cunningham
void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi!");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}


#endif
