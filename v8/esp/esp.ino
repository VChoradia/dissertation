
#include <WiFi.h>
#include <PulseSensorPlayground.h> 
#include <OneWire.h>
#include <DallasTemperature.h> 
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include <HTTPClient.h>
#include <sstream>
#include <ArduinoJson.h>
#include <AsyncEventSource.h>
#include <AsyncJson.h>
#include <AsyncWebSocket.h>
#include <AsyncWebSynchronization.h>
#include <ESPAsyncWebSrv.h>
#include <SPIFFSEditor.h>
#include <StringArray.h>
#include <WebAuthentication.h>
#include <WebHandlerImpl.h>
#include <WebResponseImpl.h>
#include <queue>

// Define the size of the moving average window
const int movingAverageWindowSize = 10;

// For BPM
float bpmSum = 0;
std::queue<int> bpmReadings;
float bpmMovingAverage = 0;

// For Temperature
float tempSum = 0;
std::queue<float> tempReadings;
float tempMovingAverage = 0;

// Tolerance constants
const int BPM_TOLERANCE = 10; // Adjust based on testing and sensor accuracy
const float TEMP_TOLERANCE = 0.5; // Adjust based on testing and sensor accuracy


AsyncWebServer server(80);
const String deviceNickname = "choradia";
const String devicePasskey = "choradia";
int device_id = -1;

String to = "";
String name = "";
int bpm_lower_threshold = 60;
int bpm_upper_threshold = 220;
int temp_lower_threshold = 32;
int temp_upper_threshold = 35;

static unsigned long lastSMSTime = 1800000;  // Last SMS send timestamp
static unsigned long lastPublishTime = 0;  // Last publish timestamp

#include "config.h"
#include "twilio_control.h"
#include "wifi_control.h"
#include "adafruit_control.h"


void setup() {

  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(SWITCH_PIN, INPUT_PULLUP); 

  setupWiFi();

  setupServer();

  setupSensors();

  MQTT_connect();

  if (!nameFeed.publish(name.c_str())) {
      Serial.println(F("Failed Name"));
    }
  

  delay(500);
  
  }

void loop() {
  int currentButtonState = digitalRead(SWITCH_PIN);
  // Check if button state has changed from LOW to HIGH (button press)
  if (currentButtonState == HIGH && lastButtonState == LOW) {
    Serial.print("Button pressed");
    isSwitchOn = !isSwitchOn;  // Toggle the publishing state
    if (isPublishing && isSwitchOn) {
      ledOn();
    } else {
      ledOff();
    }
    delay(200);  // Debounce delay
  }
  lastButtonState = currentButtonState;  // Update the last button state

  if (isPublishing && isSwitchOn) {
    publishData();
  }
}   


void publishData() {
  
  unsigned long currentMillis = millis();    // Current timestamp

  // Check if one minute has passed
  if (currentMillis - lastPublishTime >= 5000) {
    // Update last publish time
    lastPublishTime = currentMillis;

    int bpm;
    float tempC;

    // Ensure MQTT connection
    MQTT_connect();

    if (!nameFeed.publish(name.c_str())) {
      Serial.println(F("Failed Name"));
    } else {
      Serial.println(F("OK! Name"));
    }

    if (!mobileNumberFeed.publish(to.c_str())) {
      Serial.println(F("Failed Mobile Number Feed"));
    } 

    // Check for pulse and read BPM
    if (pulseSensor.sawStartOfBeat()) {
      bpm = pulseSensor.getBeatsPerMinute();
    } else {
      bpm = 0;  // Consider how you want to handle 0 BPM.
    }
    

    tempSensors.requestTemperatures();
    tempC = tempSensors.getTempCByIndex(0);

    updateMovingAverage(bpm, tempC);

    Serial.print("BPM: ");
    Serial.println(bpm);

    Serial.print("Temp: ");
    Serial.println(tempC);
    
    
     if (abs(bpm - bpmMovingAverage) < BPM_TOLERANCE && abs(tempC - tempMovingAverage) < TEMP_TOLERANCE) {

      // Publish data to MQTT
    if(bpm >0) {
      if (!bpmFeed.publish(bpm)) {
        Serial.println(F("Failed BPM"));
      }
    }
    if (!temperatureFeed.publish(tempC)) {
      Serial.println(F("Failed Temp"));
    } 
    
        if(tempC > temp_upper_threshold || tempC < temp_lower_threshold || (bpm > bpm_upper_threshold &&  bpm>0) || (bpm < bpm_lower_threshold && bpm>0) ) {
        unsigned long currentMillis = millis();  // Reuse currentMillis defined earlier in loop
        // Check if at least 30 minutes (1800000 milliseconds) have passed
        if (currentMillis - lastSMSTime >= 1800000) {
            char smsString[240]; 
            sprintf(smsString, "Patient %s's Health Alert: Body Temperature has crossed %.2f°C and current BPM is %d", name, tempC, bpm);
            if (sendSMS(smsString)) {  // Assuming sendSMS returns true if SMS was successfully sent
                lastSMSTime = currentMillis;  // Update the last SMS timestamp
                Serial.println("SMS sent successfully");
            } else {
                Serial.println("Failed to send SMS");
            }
        }
        }
     }

    sendDetails(bpm, tempC);
  }

}

void setupServer() {
    
    server.on("/stop-publishing", handleStopPublishing);

    // Handle HTTP POST request for assigning device to a user
  server.on("/receive-user-details", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, handleAssignDeviceToUser);

  // Handle HTTP POST request for unassigning device from a user
  server.on("/clear-user-details", HTTP_POST, [](AsyncWebServerRequest *request) {
    // Handle unassign device logic here
    Serial.println("Device unassigned.");
    // Reset user details
    name = "";
    to = "";
    bpm_lower_threshold = 0;
    bpm_upper_threshold = 0;
    temp_lower_threshold = 0;
    temp_upper_threshold = 0;
    request->send(200, "application/json", "{\"message\":\"Device unassigned successfully.\"}");
  });

    
  server.begin();
}



void handleStopPublishing(AsyncWebServerRequest *request)
{

    Serial.println("Received request to stop publishing data.");

    isPublishing = false;
    ledOff();
    name = "";
    to = "";
    bpm_lower_threshold = 0;
    bpm_upper_threshold = 0;
    temp_lower_threshold = 0;
    temp_upper_threshold = 0;
    
    lastSMSTime = 1800000;
    lastPublishTime = 0;
    // Code to stop publishing data goes here.
    // This could involve setting a flag that is checked in the loop() function,
    // stopping a timer, or other mechanisms depending on how data publishing is implemented.

    request->send(200, "application/json", "{\"status\":\"success\"}");
}

// Function to handle assigning device to user
void handleAssignDeviceToUser(AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, data);

  // Extract user details from the request body
  name = doc["username"].as<String>();
  to = doc["phone_number"].as<String>();
  bpm_lower_threshold = doc["bpm_lower_threshold"].as<int>();
  bpm_upper_threshold = doc["bpm_upper_threshold"].as<int>();
  temp_lower_threshold = doc["temp_lower_threshold"].as<int>();
  temp_upper_threshold = doc["temp_upper_threshold"].as<int>();

  // Log received data for debugging
  Serial.println("Received user details for device assignment:");
  Serial.print("Name: "); Serial.println(name);
  Serial.print("Phone Number: "); Serial.println(to);
  // Add more logs as needed

  isPublishing = true;

  request->send(200, "application/json", "{\"message\":\"User details received and device assigned.\"}");
}


void updateMovingAverage(int bpm, float tempC) {
    // Update BPM moving average
    if (bpmReadings.size() >= movingAverageWindowSize) {
        bpmSum -= bpmReadings.front();
        bpmReadings.pop();
    }
    bpmSum += bpm;
    bpmReadings.push(bpm);
    bpmMovingAverage = bpmSum / bpmReadings.size();

    // Update Temperature moving average
    if (tempReadings.size() >= movingAverageWindowSize) {
        tempSum -= tempReadings.front();
        tempReadings.pop();
    }
    tempSum += tempC;
    tempReadings.push(tempC);
    tempMovingAverage = tempSum / tempReadings.size();
}
