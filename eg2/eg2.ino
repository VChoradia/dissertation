#include <WiFi.h>
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

AsyncWebServer server(80);
const String devicePasskey = "vivek";

// network credentials
const char *ssid = "uos-other";
const char *password = "shefotherkey05";

String name;
String to;

int bpm_upper_threshold;
int bpm_lower_threshold;
int temp_upper_threshold;
int temp_lower_threshold;

bool isPublishing = false;
bool isSwitchOn = false;


// Adapted from COM 3505 Internet of Things Weekly Lab Solutions authored by Prof. Hamish Cunningham
void setupWiFi()
{
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi!");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());
}

void setup()
{
  // Initialize server and Wi-Fi as usual

  Serial.begin(115200);

  while (!Serial);

  setupWiFi();

  setupServer();
}

void loop()
{
  Serial.println(name);
  delay(10000);
}

void setupServer() {
    server.on("/verify", handleVerify);
    
    server.on("/receive-user-data", HTTP_POST, [](AsyncWebServerRequest *request) {
        // You might want to handle any non-body part of the request here
    }, NULL, [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
        // Now call your external function
        handleReceiveUserData(request, data, len, index, total); // Adjust the signature accordingly
    });
    
    server.on("/stop-publishing", handleStopPublishing);

    
  server.begin();
}

void handleVerify(AsyncWebServerRequest *request)
{

    Serial.println("Received verify request");
    // Check if the passkey parameter exists to avoid potential null pointer dereference
    if (!request->hasParam("passkey"))
    {
        request->send(400, "application/json", "{\"error\":\"passkey parameter is missing\"}");
        return;
    }

    // Now it's safe to assume the parameter exists
    String passkey = request->getParam("passkey")->value();
    bool verified = passkey.equals(devicePasskey); // Assuming devicePasskey is defined elsewhere

    // Use the corrected case for the JSON key as per your requirement
    DynamicJsonDocument doc(1024);
    doc["verified"] = verified; // Capital 'V' as per your requirement
    String response;
    serializeJson(doc, response);

    request->send(200, "application/json", response);
}

void handleReceiveUserData(AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total)
{

    DynamicJsonDocument doc(1024); // Adjust size according to your data structure
    DeserializationError error = deserializeJson(doc, data);

    if (error)
    {
        Serial.print(F("deserializeJson() failed: "));
        Serial.println(error.f_str());
        request->send(400, "application/json", "{\"message\":\"Invalid JSON\"}");
        return;
    }

    name = doc["userName"].as<String>();
    to = doc["phoneNumber"].as<String>();
    bpm_lower_threshold = doc["bpmLowerThreshold"].as<int>();
    bpm_upper_threshold = doc["bpmUpperThreshold"].as<int>();
    temp_lower_threshold = doc["tempUpperThreshold"].as<int>();
    temp_upper_threshold = doc["tempLowerThreshold"].as<int>();

    Serial.println("Received User Data:");
    Serial.print("Name: ");
    Serial.println(name);
    Serial.print("Phone: ");
    Serial.println(to);

    isPublishing = true;

    request->send(200, "application/json", "{\"status\":\"success\"}");
}

void handleStopPublishing(AsyncWebServerRequest *request)
{

    Serial.println("Received request to stop publishing data.");

    isPublishing = false;
    name = "";
    to = "";
    // Code to stop publishing data goes here.
    // This could involve setting a flag that is checked in the loop() function,
    // stopping a timer, or other mechanisms depending on how data publishing is implemented.

    request->send(200, "application/json", "{\"status\":\"success\"}");
}
