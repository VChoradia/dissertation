#include <WiFi.h>
#include <ArduinoJson.h> 

const char* ssid = "uos-other";
const char* password = "shefotherkey05";
const char* host = "143.167.38.207"; 
const uint16_t httpPort = 5000; // Flask default port is 5000

void setup() {
  Serial.begin(115200);
  while(!Serial);
  delay(10);

  // Connect to WiFi network
  Serial.println();
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // Make a HTTP GET request
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

  DynamicJsonDocument doc(1024);
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
  const char* name = doc["name"]; 
  const char* to = doc["to"]; 

  Serial.print("Name: ");
  Serial.println(name);
  Serial.print("To: ");
  Serial.println(to);
}

void loop() {
  // Empty loop
}
