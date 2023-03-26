#include <Adafruit_MAX31856.h>

std::array<Adafruit_MAX31856, 2> thermocouples = {
  Adafruit_MAX31856(27,14,12,13),
  Adafruit_MAX31856(21,19,18,5),
};

void setup() {
  Serial.begin(9600);
  // Initialize the thermocouples.
  for (auto& tc : thermocouples) {
    tc.begin();
    tc.setThermocoupleType(MAX31856_TCTYPE_K);
    tc.setConversionMode(MAX31856_CONTINUOUS);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String rx = Serial.readStringUntil('\n');
    if (rx.equals("*IDN?")) {
      Serial.println("ESP32");
    } else if (rx.equals("GET TEMP")) {
      float temp0 = thermocouples[0].readThermocoupleTemperature();
      float temp1 = thermocouples[1].readThermocoupleTemperature();
      Serial.printf("%f,%f\n", temp0, temp1);
    }
  }
}
