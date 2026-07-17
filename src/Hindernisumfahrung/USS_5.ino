#include <Arduino.h>

// Ein Sensor pro Richtung; die Reihenfolge legt das Offset-Schema fest,
// mit dem alle fünf Distanzen über eine einzige serielle Verbindung
// codiert werden (siehe encodeDistance()).
struct UltrasonicSensor {
  uint8_t trigPin;
  uint8_t echoPin;
  uint16_t offset;
};

const uint8_t SENSOR_COUNT = 5;
const uint16_t OFFSET_STEP = 500;
const unsigned long PULSE_TIMEOUT_US = 30000UL;  // ~5 m maximale Reichweite
const float US_TO_CM = 29.1f;
const int LOOP_DELAY_MS = 500;

UltrasonicSensor sensors[SENSOR_COUNT] = {
  {8, 9, 0 * OFFSET_STEP},    // Sensor 1 – Vorne
  {7, 10, 1 * OFFSET_STEP},   // Sensor 2 – Vorne Rechts
  {4, 5, 2 * OFFSET_STEP},    // Sensor 3 – Vorne Links
  {2, 3, 3 * OFFSET_STEP},    // Sensor 4 – Rechts
  {12, 11, 4 * OFFSET_STEP},  // Sensor 5 – Links
};

void setup() {
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    pinMode(sensors[i].trigPin, OUTPUT);
    pinMode(sensors[i].echoPin, INPUT);
  }
  Serial.begin(9600);
}

long measureDistanceCm(const UltrasonicSensor &sensor) {
  digitalWrite(sensor.trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(sensor.trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(sensor.trigPin, LOW);

  long duration = pulseIn(sensor.echoPin, HIGH, PULSE_TIMEOUT_US);
  if (duration == 0) {
    return OFFSET_STEP - 1;  // kein Echo empfangen: als maximale Distanz werten
  }
  return (duration / 2) / US_TO_CM;
}

long encodeDistance(long distanceCm, uint16_t offset) {
  if (distanceCm >= OFFSET_STEP) {
    distanceCm = OFFSET_STEP - 1;
  }
  return distanceCm + offset;
}

void loop() {
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    long distanceCm = measureDistanceCm(sensors[i]);
    Serial.println(encodeDistance(distanceCm, sensors[i].offset));
    delay(LOOP_DELAY_MS);
  }
}
