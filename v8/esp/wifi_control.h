#ifndef WIFI_CONTROL_H
#define WIFI_CONTROL_H

#include <WiFi.h>
#include <HTTPClient.h>

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

  // Prepare the JSON payload as a String
  String payload = "{\"mac_address\":\"" + WiFi.macAddress() + "\",";
  payload += "\"ip_address\":\"" + WiFi.localIP().toString() + "\",";
  payload += "\"passkey\":\""+devicePasskey+ "\",";
  payload += "\"nickname\":\"" + deviceNickname + "\"}";

  // Create an HTTPClient object
  HTTPClient http;
  
  // Specify the URL for the POST request
  http.begin("http://143.167.38.140:5500/add-new-device");
  http.addHeader("Content-Type", "application/json");

  // Send the POST request
  int httpResponseCode = http.POST(payload);

  // Check the response
  if(httpResponseCode>0) {
    String response = http.getString(); // Get the response to the request
    Serial.println(httpResponseCode);   // Print return code
    Serial.println(response);           // Print request answer
    
    // Parse JSON response
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, response);
    
    // Extract device_id (assuming the server responds with a JSON object that includes device_id)
    if (doc.containsKey("device_id")) {
      device_id = doc["device_id"]; // Store the device ID in the global variable
      Serial.print("Device ID: ");
      Serial.println(device_id);
    } else {
      Serial.println("Device ID not received in the response");
    }
  } else {
    Serial.print("Error on sending POST: ");
    Serial.println(httpResponseCode);
  }

  // End the HTTP connection
  http.end();
}


#endif
