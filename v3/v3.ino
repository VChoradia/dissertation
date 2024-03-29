/**
 * Author: Vivek Choradia
 * Script to run Pimoroni Pulse Sensor and DS18b20 Temperature sensor consecutively. The data is then averaged out before printing.
 */

 // Libraries
#include <PulseSensorPlayground.h> 
#include <OneWire.h>
#include <DallasTemperature.h> 

// Pulse Sensor Setup
const int PulseWire = 11;
int Threshold = 550; // Determine which Signal to "count as a beat" and which to ignore.
PulseSensorPlayground pulseSensor;

// DS18b20 Sensor Setup
const int TempWire = 10;
OneWire oneWire(TempWire);
DallasTemperature tempSensors(&oneWire);


void setup() {

  Serial.begin(9600);

  // PulseSensor configuration
  pulseSensor.analogInput(PulseWire);
  pulseSensor.setThreshold(Threshold);
  if (pulseSensor.begin()) {
    Serial.println("PulseSensor initialised!");
  } else {
    Serial.print("PulseSensor failed");
  }

  // DS18b20 configuration
  tempSensors.begin();

}

void loop() {
  if (pulseSensor.sawStartOfBeat()) {
    int myBPM = pulseSensor.getBeatsPerMinute();
    Serial.print("BPM: ");
    Serial.println(myBPM);
  }

  tempSensors.requestTemperatures();
  float tempC = tempSensors.getTempCByIndex(0);
  Serial.print("Temperature: ");
  Serial.print(tempC);
  Serial.println(" ºC");

  delay(5000);

}
