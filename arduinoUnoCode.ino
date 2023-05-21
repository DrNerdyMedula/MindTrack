#include <LiquidCrystal.h>

//fan:
#define ENABLE 5
#define DIRA 3
#define DIRB 4

const int rs = 7, en = 8, d4 = 9, d5 = 10, d6 = 11, d7 = 12; //make sure these are plugged in right
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

int buzzer = 13; //the pin of the active buzzer
int onCommandCounter = 0; // Add a counter for the 'on' command
unsigned char i;

void setup() {
  lcd.begin(16, 2); // This is for the LCD startup, setting rows and columns
  lcd.print("HACK-DAVIS_2023");
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(57600);
  pinMode(buzzer, OUTPUT); //initialize the buzzer pin as an output
  
  // Fan:
  pinMode(ENABLE,OUTPUT);
  pinMode(DIRA,OUTPUT);
  pinMode(DIRB,OUTPUT);
  Serial.begin(57600);
}

void loop() {
  lcd.setCursor(0, 1);
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command.startsWith("digitalWrite 14 1")) {
      onCommandCounter++; // Increment the counter when the 'on' command is received
      digitalWrite(ENABLE, LOW); // For Fan
      if (onCommandCounter >= 110) { // If the 'on' command has been received 100 times or more
        digitalWrite(LED_BUILTIN, HIGH); // Turn the LED on
        lcd.print("                "); // clear the display
        lcd.setCursor(0, 1); // reset the cursor
        //lcd.print(data1);
        lcd.print("[User Unfocused]"); // sends a signal that the user is focused
        onCommandCounter = 0;
        
          for (i = 0; i < 2; i++) {
            digitalWrite(buzzer, HIGH);
            delay(100); //wait for 1ms
            digitalWrite(buzzer, LOW);
            delay(100); //wait for 1ms
          }
        
      }
    } else if (command.startsWith("digitalWrite 14 0")) {
      digitalWrite(LED_BUILTIN, LOW);// Turn the LED off
      digitalWrite(buzzer, LOW); 
      lcd.print("                "); // clear the display
      lcd.setCursor(0, 1); // reset the cursor
      //lcd.print(data1);
      lcd.print("[User Focused]"); // sends a signal that the user is not focused
      onCommandCounter = 0; // Reset the counter when the LED is turned off

      // Fan:
      analogWrite(ENABLE, 225);
      digitalWrite(DIRA,HIGH); //one way
      digitalWrite(DIRB,LOW);
      delay(20);
    }
  }
}