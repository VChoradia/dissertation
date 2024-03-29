#include <PulseSensorPlayground.h> // Includes the PulseSensorPlayground Library for the heartbeat sensor

// PulseSensor Setup
const int PulseWire = 11; 
const int LED = LED_BUILTIN;
int Threshold = 550; // Determine which Signal to "count as a beat" and which to ignore.
PulseSensorPlayground pulseSensor;

// LM35 Temperature Sensor Setup
#define ADC_VREF_mV 1100.0 // in millivolt, for LM35 temperature calculation
#define ADC_RESOLUTION 4096.0
#define PIN_LM35 6 

// Arrays to store readings
int bpmReadings[60]; // Store 60 BPM readings
float tempReadings[60]; // Store 60 temperature readings
int readingsIndex = 0; // Index for the readings arrays

void setup() {
  Serial.begin(9600); // For Serial Monitor

  pinMode(PIN_LM35, INPUT);

  // PulseSensor configuration
  pulseSensor.analogInput(PulseWire);
  pulseSensor.blinkOnPulse(LED); // Auto-magically blink Arduino's LED with heartbeat.
  pulseSensor.setThreshold(Threshold);
  if (pulseSensor.begin()) {
    Serial.println("PulseSensor initialized!");
  }

  // Initialize readings arrays
  for (int i = 0; i < 60; i++) {
    bpmReadings[i] = 0;
    tempReadings[i] = 0.0;
  }
}

void loop() {
  // PulseSensor reading
  if (pulseSensor.sawStartOfBeat()) {
    int myBPM = pulseSensor.getBeatsPerMinute();
    bpmReadings[readingsIndex] = myBPM; // Store BPM reading
  }

  // LM35 Temperature Sensor reading
  int adcVal = analogRead(PIN_LM35);
  float milliVolt = adcVal * (ADC_VREF_mV / ADC_RESOLUTION);
  float tempC = milliVolt / 10;
  tempReadings[readingsIndex] = tempC; // Store temperature reading

  Serial.print(tempC);
//  readingsIndex++;
  
//  if (readingsIndex >= 60) { // After 60 readings, process data
//    Serial.print("Average BPM: ");
//    Serial.println(calculateBPMAverage(bpmReadings, 60, true)); // Calculate and print average BPM, exclude extremes
//    Serial.print("Average Temperature: ");
//    Serial.println(calculateTempAverage(tempReadings, 60, false)); // Calculate and print average temperature, exclude extremes
//    readingsIndex = 0; // Reset index
//  }

  delay(1000); // Delay for a second
}

float calculateBPMAverage(int readings[], int numReadings, bool isBPM) {
  float sum = 0;
  int validReadings = 0;
  int excludeCount = numReadings * 0.1; // Exclude top and bottom 10%

  // Sort the array
  for (int i = 0; i < numReadings-1; i++) {
    for (int j = i+1; j < numReadings; j++) {
      if (readings[i] > readings[j]) {
        int temp = readings[i];
        readings[i] = readings[j];
        readings[j] = temp;
      }
    }
  }

  // Calculate sum excluding extremes
  for (int i = excludeCount; i < numReadings - excludeCount; i++) {
    sum += readings[i];
    validReadings++;
  }

  // Calculate and return average
  if (validReadings > 0) return sum / validReadings;
  else return 0;
}

float calculateTempAverage(float readings[], int numReadings, bool isTemp) {
  float sum = 0;
  int validReadings = 0;
  int excludeCount = numReadings * 0.1; // Exclude top and bottom 10%

  // Sort the array
  for (int i = 0; i < numReadings-1; i++) {
    for (int j = i+1; j < numReadings; j++) {
      if (readings[i] > readings[j]) {
        float temp = readings[i];
        readings[i] = readings[j];
        readings[j] = temp;
      }
    }
  }

  // Calculate sum excluding extremes
  for (int i = excludeCount; i < numReadings - excludeCount; i++) {
    sum += readings[i];
    validReadings++;
  }

  // Calculate and return average
  if (validReadings > 0) return sum / validReadings;
  else return 0;
}
