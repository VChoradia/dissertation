#ifndef CONFIG_H
#define CONFIG_H

#include <WiFi.h>
#include <PulseSensorPlayground.h> 
#include <OneWire.h>
#include <DallasTemperature.h> 
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include <HTTPClient.h>
#include <sstream>
#include <ArduinoJson.h>


#define SWITCH_PIN 12
#define LED_PIN 13

bool isPublishing = false;  // State variable to keep track of publishing status
int lastButtonState = LOW;  // Last state of the button


const char* host = "143.167.39.80"; // IP address of your server
const uint16_t httpPort = 5000; // Flask default port is 5000
String serverName = "http://" + String(host) + ":" + String(httpPort) + "/sendDetails";

WiFiClient espClient;

// Pulse Sensor Setup
const int PulseWire = 11;
int Threshold = 550; 
PulseSensorPlayground pulseSensor;

// DS18b20 Sensor Setup
const int TempWire = 10;
OneWire oneWire(TempWire);
DallasTemperature tempSensors(&oneWire);

void setupSensors() {
    // Pulse Sensor Configurations
    pulseSensor.analogInput(PulseWire);
    pulseSensor.setThreshold(Threshold);
    if (pulseSensor.begin()) {
        Serial.println("PulseSensor initialised!");
    }

    // DS18b20 Configuration
    tempSensors.begin();
}

void ledOn()  {
  digitalWrite(LED_PIN, HIGH);
}
void ledOff() {
  digitalWrite(LED_PIN, LOW);
}

void getDetails() {

   WiFiClient client;
  if (!client.connect(host, httpPort)) {
    Serial.println("Connection failed");
    return;
  }

  // This will send the request to the server
  client.print(String("GET ") + "/getDetails" + " HTTP/1.1\r\n" +
               "Host: " + host + "\r\n" +
               "Connection: close\r\n\r\n");
  delay(500); // Wait for server to respond

  // Initialize the JSON Document
  DynamicJsonDocument doc(1024);

  // Read all the lines of the reply from server and deserialize the JSON content
  String line;
  while (client.available()) {
    line = client.readStringUntil('\r');
  }

  // Use ArduinoJson to deserialize the JSON
  DeserializationError error = deserializeJson(doc, line);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Extract the values
  name = doc["name"].as<String>(); 
  to = doc["to"].as<String>(); 
  bpm_lower_threshold = doc["bpm_lower_threshold"].as<int>();
  bpm_upper_threshold = doc["bpm_upper_threshold"].as<int>();
  temp_lower_threshold = doc["temp_lower_threshold"].as<int>();
  temp_upper_threshold = doc["temp_upper_threshold"].as<int>();
  }

  void sendDetails(int bpm, float temp) {
  // Check WiFi connection status
  if(WiFi.status()== WL_CONNECTED){
    HTTPClient http;

    // Your JSON data
    const int capacity = JSON_OBJECT_SIZE(2); // Adjust based on the number of fields
    StaticJsonDocument<capacity> doc;
    doc["bpm"] = bpm;
    doc["temp"] = temp;

    // Serialize JSON data
    String jsonData;
    serializeJson(doc, jsonData);

    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonData);

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    // Free resources
    http.end();
  }
  else {
    Serial.println("WiFi Disconnected");
  }
}

#endif 
