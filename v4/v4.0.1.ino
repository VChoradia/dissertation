#include <WiFi.h>
#include <PubSubClient.h>
#include <PulseSensorPlayground.h> 
#include <OneWire.h>
#include <DallasTemperature.h> 
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"

// network credentials
const char* ssid = "uos-other";
const char* password = "shefotherkey05";

#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883
#define AIO_USERNAME    "vivekchoradia"
#define AIO_KEY         "aio_Kfxi61SutR9ooklPO22ALLfRb2kB"

WiFiClient espClient;

// Pulse Sensor Setup
const int PulseWire = 11;
int Threshold = 550; 
PulseSensorPlayground pulseSensor;

// DS18b20 Sensor Setup
const int TempWire = 9;
OneWire oneWire(TempWire);
DallasTemperature tempSensors(&oneWire);


// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
Adafruit_MQTT_Client mqtt(&espClient, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);
Adafruit_MQTT_Publish bpmFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/BPM");
Adafruit_MQTT_Publish temperatureFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/Temperature");

void setup() {

  Serial.begin(9600);


  // Setup Sensors

  // Pulse Sensor Configurations
    pulseSensor.analogInput(PulseWire);
  pulseSensor.setThreshold(Threshold);
  if (pulseSensor.begin()) {
    Serial.println("PulseSensor initialised!");
  }

  // DS18b20 Configuration
  tempSensors.begin();

  
  }

void loop() {
  static unsigned long lastPublishTime = 0;  // Last publish timestamp
  unsigned long currentMillis = millis();    // Current timestamp

  if (currentMillis - lastPublishTime >= 3000) {
    // Update last publish time
    lastPublishTime = currentMillis;

    int bpm;
    float tempC;

   

    // Check for pulse and read BPM
    if (pulseSensor.sawStartOfBeat()) {
      bpm = pulseSensor.getBeatsPerMinute();
    } 

    Serial.print("BPM: ");
    Serial.println(bpm);
    
    tempSensors.requestTemperatures();
    tempC = tempSensors.getTempCByIndex(0);

    Serial.print("Temperature: ");
    Serial.println(tempC);

  }
  
}


void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi!");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
}

void MQTT_connect()
{
  int8_t ret;
  if (mqtt.connected()) {
    return;
  }

  uint8_t retries = 3;

  while ((ret = mqtt.connect()) != 0) { 
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("Retrying MQTT connection in 5 seconds...");
    mqtt.disconnect();

    delay(5000);

    retries--;
    if (retries == 0) {
      while (1);
    }
  }
}
