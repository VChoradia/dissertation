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


// network credentials
const char* ssid = "uos-other";
const char* password = "shefotherkey05";

#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883
#define AIO_USERNAME    "vivekchoradia"
#define AIO_KEY         "aio_Kfxi61SutR9ooklPO22ALLfRb2kB"

const char* host = "143.167.38.207"; // IP address of your server
const uint16_t httpPort = 5000; // Flask default port is 5000

WiFiClient espClient;

// Pulse Sensor Setup
const int PulseWire = 11;
int Threshold = 550; 
PulseSensorPlayground pulseSensor;

// DS18b20 Sensor Setup
const int TempWire = 10;
OneWire oneWire(TempWire);
DallasTemperature tempSensors(&oneWire);


// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
Adafruit_MQTT_Client mqtt(&espClient, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);
Adafruit_MQTT_Publish bpmFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/BPM");
Adafruit_MQTT_Publish temperatureFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/Temperature");
Adafruit_MQTT_Publish nameFeed  = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/Device-1");
Adafruit_MQTT_Publish mobileNumberFeed  = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/mobile-number");


// Values from Twilio (find them on the dashboard)
static const char *messagingServiceSid = "MG1d0e0fbab08bc7bea54d0ed6a8e41fe2";
static const char *twilioPassword = "2abe873f1c88ef7c44869f000d6d7675";
static const char *accountNr = "AC585120fa3d6b1456caedd48dbd60af28";
String to = "+447387210693";

String name = "Vivek Choradia";

static unsigned long lastSMSTime = 1800000;  // Last SMS send timestamp
static unsigned long lastPublishTime = 0;  // Last publish timestamp

void setup() {

  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(SWITCH_PIN, INPUT_PULLUP); 

  setupWiFi();

  // Setup Sensors

  // Pulse Sensor Configurations
    pulseSensor.analogInput(PulseWire);
  pulseSensor.setThreshold(Threshold);
  if (pulseSensor.begin()) {
    Serial.println("PulseSensor initialised!");
  }

  // DS18b20 Configuration
  tempSensors.begin();

  getDetails();

  MQTT_connect();

  if (!nameFeed.publish(name.c_str())) {
      Serial.println(F("Failed Name"));
    } else {
      Serial.println(F("OK! Name"));
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


// Adapted from COM 3505 Internet of Things Weekly Lab Solutions authored by Prof. Hamish Cunningham
void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi!");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
}

// Adapted from https://www.cytron.io/tutorial/send-sensors-data-to-adafruit-io-using-esp32
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
      // basically die and wait for WDT to reset me
      while (1);
    }
  }
}

// Adapted from https://techtutorialsx.com/2021/12/01/esp32-sending-an-sms-with-twilio/
bool sendSMS(const char * body){
 
  std::stringstream url;
  url << "https://api.twilio.com/2010-04-01/Accounts/" << accountNr <<"/Messages";
 
  std::stringstream urlEncodedBody;
  urlEncodedBody << "MessagingServiceSid=" << messagingServiceSid << "&To=" << to.c_str() << "&Body=" << body;
 
  Serial.print("\nURL: ");
  Serial.println(url.str().c_str());
  Serial.print("Encoded body: ");
  Serial.println(urlEncodedBody.str().c_str());
   
 
  HTTPClient http;
 
  http.begin(url.str().c_str());
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  http.setAuthorization(accountNr, twilioPassword);
   
  int httpCode = http.POST(urlEncodedBody.str().c_str());                                               
  
  if (httpCode > 0) {
 
      String payload = http.getString();
 
      Serial.print("\nHTTP code: ");
      Serial.println(httpCode);
 
      Serial.print("\nResponse: ");
      Serial.println(payload);
    }
 
  else {
    Serial.println("Error on HTTP request:");
    Serial.println(httpCode);
  }
 
  http.end();
 
  return httpCode == 201;
 
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
    } else {
      Serial.println(F("OK! Mobile Number Feed"));
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
    } else {
      Serial.println(F("OK! BPM"));
    }

    tempSensors.requestTemperatures();
    tempC = tempSensors.getTempCByIndex(0);

    // Publish temperature to MQTT
    if (!temperatureFeed.publish(tempC)) {
      Serial.println(F("Failed Temp"));
    } else {
      Serial.println(F("OK! Temp"));
    }

    if(tempC > 35) {
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
  }
