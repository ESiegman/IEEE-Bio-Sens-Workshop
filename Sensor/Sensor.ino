#define EMG A7

void setup() {
    Serial.begin(9600);
    pinMode(EMG, INPUT);
}

void loop() {

    int sensorValue = analogRead(A7);
    Serial.println(sensorValue);
    delay(1);
}
