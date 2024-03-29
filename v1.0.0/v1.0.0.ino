#include <PulseSensorPlayground.h> // Includes the PulseSensorPlayground Library for the heartbeat sensor

// PulseSensor Setup
const int PulseWire = A4; 
const int LED = LED_BUILTIN;
int Threshold = 550; // Determine which Signal to "count as a beat" and which to ignore.
PulseSensorPlayground pulseSensor;

// LM35 Temperature Sensor Setup
#define ADC_VREF_mV 1100.0 // in millivolt, for LM35 temperature calculation
#define ADC_RESOLUTION 4096.0
#define PIN_LM35 6 

void setup() {
  Serial.begin(9600); // For Serial Monitor

  pinMode(PIN_LM35, INPUT);

  // PulseSensor configuration
  pulseSensor.analogInput(PulseWire);
  pulseSensor.blinkOnPulse(LED); // Auto-magically blink Arduino's LED with heartbeat.
  pulseSensor.setThreshold(Threshold);
  if (pulseSensor.begin()) {
    Serial.println("pulseSensor Object created!");
  }

}

void loop() {
  // PulseSensor reading and display
  if (pulseSensor.sawStartOfBeat()) { // Constantly test to see if "a beat happened".
    int myBPM = pulseSensor.getBeatsPerMinute(); // Calls function on pulseSensor object that returns BPM as an "int".
    Serial.print("BPM: "); 
    Serial.println(myBPM); 
  }

  // LM35 Temperature Sensor reading and display
  int adcVal = analogRead(PIN_LM35); // Get the ADC value from the temperature 
  
  float milliVolt =  adcVal * (ADC_VREF_mV / ADC_RESOLUTION); // Convert the ADC value to voltage in millivolt
  float tempC = milliVolt / 10; // Convert the voltage to the temperature in Celsius
  Serial.print("Temperature: ");
  Serial.print(tempC); 
  Serial.println("°C");

  delay(1000); 
}
