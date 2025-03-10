#define EMG A0

void setup() {
    Serial.begin(9600);
    pinMode(EMG, INPUT);
}

void loop() {

    float rawSensorValue = analogRead(EMG);
    float convertedVoltage = map(rawSensorValue, 0, 1023, 0, 5);
    Serial.println(rawSensorValue);
    delay(1);
}
