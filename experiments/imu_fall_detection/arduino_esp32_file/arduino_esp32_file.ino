#include <WiFi.h>
#include <WebServer.h>

// The ESP32 Hotspot Name
const char* ssid = "<CONFIGURE_LOCALLY>"; 

// Your working LED Pin!
const int LED_PIN = 33;

WebServer server(80);

// --- Stopwatch Variables ---
unsigned long alarmStartTime = 0;
bool isAlarmActive = false;
const unsigned long ALARM_DURATION = 5000; // 5 seconds

void setup() {
  Serial.begin(115200);
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // Start with LED OFF

  Serial.println();
  Serial.println("--- Starting ESP32 Hotspot ---");
  WiFi.softAP(ssid);
  
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.softAPIP()); 

  server.on("/trigger_alarm", HTTP_POST, []() {
    Serial.println("\n🚨 EMERGENCY: FALL SIGNAL RECEIVED! 🚨");
    server.send(200, "application/json", "{\"status\":\"success\"}");
    
    // TURN THE LED ON!
    digitalWrite(LED_PIN, HIGH);
    
    // Start the stopwatch
    isAlarmActive = true;
    alarmStartTime = millis(); 
  });

  server.begin();
  Serial.println("HTTP server started!");
}

void loop() {
  // Keep the Wi-Fi running smoothly
  server.handleClient();

  // Check the stopwatch every millisecond
  if (isAlarmActive) {
    if (millis() - alarmStartTime >= ALARM_DURATION) {
      // Time is up! Turn it off!
      digitalWrite(LED_PIN, LOW);
      
      isAlarmActive = false; // Reset the stopwatch
      Serial.println("Alarm reset. LED OFF. Listening...");
    }
  }
}