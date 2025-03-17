#include <avr/sleep.h>

#define SENSOR_PIN 3  // D3
#define LED_PIN 13

void setup() {
    pinMode(SENSOR_PIN, INPUT_PULLUP);  
    pinMode(LED_PIN, OUTPUT);
    Serial.begin(9600);
}

void goToSleep() {
    set_sleep_mode(SLEEP_MODE_IDLE); 
    sleep_enable();
    sleep_cpu();                           //Tu śpi jak cos
    sleep_disable();
}

void loop() {
    if (Serial.available() > 0) {  
        char received = Serial.read();  
        if (received == '?') {            //Odpowiada tylko na znak zapytania
            int value = digitalRead(SENSOR_PIN);
            Serial.println(value);

            digitalWrite(LED_PIN, HIGH);
            delay(200);
            digitalWrite(LED_PIN, LOW);
        }
    }
    
    goToSleep(); 
}
