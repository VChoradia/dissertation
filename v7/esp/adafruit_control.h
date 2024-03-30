#ifndef ADAFRUIT_CONTROL_H
#define ADAFRUIT_CONTROl_H

#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"

#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883
#define AIO_USERNAME    "vivekchoradia"
#define AIO_KEY         "aio_Kfxi61SutR9ooklPO22ALLfRb2kB"


// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
Adafruit_MQTT_Client mqtt(&espClient, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);
Adafruit_MQTT_Publish bpmFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/BPM");
Adafruit_MQTT_Publish temperatureFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/Temperature");
Adafruit_MQTT_Publish nameFeed  = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/Device-1");
Adafruit_MQTT_Publish mobileNumberFeed  = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/mobile-number");

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



#endif