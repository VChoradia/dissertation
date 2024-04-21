#ifndef TWILIO_CONTROL_H
#define TWILIO_CONTROL_H

#include <HTTPClient.h>
#include <sstream>

// Values from Twilio (find them on the dashboard)
static const char *messagingServiceSid = "MG1d0e0fbab08bc7bea54d0ed6a8e41fe2";
static const char *twilioPassword = "2abe873f1c88ef7c44869f000d6d7675";
static const char *accountNr = "AC585120fa3d6b1456caedd48dbd60af28";

// Adapted from https://techtutorialsx.com/2021/12/01/esp32-sending-an-sms-with-twilio/
bool sendSMS(const char * body){
 
  std::stringstream url;
  url << "https://api.twilio.com/2010-04-01/Accounts/" << accountNr <<"/Messages";
 
  std::stringstream urlEncodedBody;
  urlEncodedBody << "MessagingServiceSid=" << messagingServiceSid << "&To=" << to.c_str() << "&Body=" << body;
 
  // Serial.print("\nURL: ");
  // Serial.println(url.str().c_str());
  // Serial.print("Encoded body: ");
  // Serial.println(urlEncodedBody.str().c_str());
   
 
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
    } else {
    Serial.println("Error on HTTP request:");
    Serial.println(httpCode);
  }
 
  http.end();
 
  return httpCode == 201;
 
}


#endif 