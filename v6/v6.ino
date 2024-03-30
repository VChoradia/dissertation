
#include <WiFi.h>
#include <PulseSensorPlayground.h> 
#include <OneWire.h>
#include <DallasTemperature.h> 
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include <HTTPClient.h>
#include <sstream>
#include <ArduinoJson.h>

String to = "+447387210693";
String name = "Vivek Choradia";
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

  setupSensors();

  getDetails();

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
    isPublishing = !isPublishing;  // Toggle the publishing state
    if (isPublishing) {
      ledOn();
    } else {
      ledOff();
    }
    delay(200);  // Debounce delay
  }
  lastButtonState = currentButtonState;  // Update the last button state

  if (isPublishing) {
    publishData();
  }
}   


void publishData() {

  getDetails();

  
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

    // Publish BPM to MQTT
    if (!bpmFeed.publish(bpm)) {
      Serial.println(F("Failed BPM"));
    }

    tempSensors.requestTemperatures();
    tempC = tempSensors.getTempCByIndex(0);

    // Publish temperature to MQTT
    if (!temperatureFeed.publish(tempC)) {
      Serial.println(F("Failed Temp"));
    } 

    if(tempC > temp_upper_threshold || tempC < temp_lower_threshold || bpm > bpm_upper_threshold || bpm < bpm_lower_threshold ) {
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

    sendDetails(bpm, tempC);
  }

}
