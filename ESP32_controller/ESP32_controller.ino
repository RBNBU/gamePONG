#include <esp_now.h>
#include <WiFi.h>

uint8_t gatewayAddress[] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF}; 

const int BUTTON_UP_PIN = 2;
const int BUTTON_DOWN_PIN = 4;

esp_now_peer_info_t peerInfo;

int lastButtonUpState = HIGH;
int lastButtonDownState = HIGH;
int currentButtonUpState;
int currentButtonDownState;

String lastMessageSent = "";

unsigned long lastDebounceTimeUp = 0;
unsigned long lastDebounceTimeDown = 0;
unsigned long debounceDelay = 50;


void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("ESP-NOW Send Status: ");
  if (status == ESP_NOW_SEND_SUCCESS) {
    Serial.println("Delivery success");
  } else {
    Serial.println("Delivery fail");
  }
}

void sendEspNowMessage(const char* message) {
  if (message == nullptr) return;

  if (String(message) != lastMessageSent || (String(message) != "hold")) {
    esp_err_t result = esp_now_send(gatewayAddress, (uint8_t *) message, strlen(message));
    
    if (result == ESP_OK) {
      Serial.print("Sent message: ");
      Serial.println(message);
      lastMessageSent = message;
    } else {
      Serial.print("Error sending message: ");
      Serial.println(message);
    }
  } else if (String(message) == "hold" && lastMessageSent != "hold") {
     esp_err_t result = esp_now_send(gatewayAddress, (uint8_t *) message, strlen(message));
    if (result == ESP_OK) {
      Serial.print("Sent message (transition to hold): ");
      Serial.println(message);
      lastMessageSent = message;
    } else {
      Serial.print("Error sending message (transition to hold): ");
      Serial.println(message);
    }
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial); 

  Serial.println("ESP32 ESP-NOW Button Sender");

  WiFi.mode(WIFI_STA);
  Serial.print("This ESP32 (Sender) MAC Address: ");
  Serial.println(WiFi.macAddress()); 

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  Serial.println("ESP-NOW Initialized.");

  esp_now_register_send_cb(OnDataSent);

  memcpy(peerInfo.peer_addr, gatewayAddress, 6);
  peerInfo.channel = 0; 
  peerInfo.encrypt = false; 
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK){
    Serial.println("Failed to add peer");
    return;
  }
  Serial.println("Peer (Gateway) Added.");

  pinMode(BUTTON_UP_PIN, INPUT_PULLUP);
  pinMode(BUTTON_DOWN_PIN, INPUT_PULLUP);

  Serial.println("Setup complete. Ready to send button states.");
}

void loop() {
  int readingUp = digitalRead(BUTTON_UP_PIN);
  if (readingUp != lastButtonUpState) {
    lastDebounceTimeUp = millis();
  }
  if ((millis() - lastDebounceTimeUp) > debounceDelay) {
    if (readingUp != currentButtonUpState) {
      currentButtonUpState = readingUp;
    }
  }
  lastButtonUpState = readingUp;

  int readingDown = digitalRead(BUTTON_DOWN_PIN);
  if (readingDown != lastButtonDownState) {
    lastDebounceTimeDown = millis();
  }
  if ((millis() - lastDebounceTimeDown) > debounceDelay) {
    if (readingDown != currentButtonDownState) {
      currentButtonDownState = readingDown;
    }
  }
  lastButtonDownState = readingDown;


  if (currentButtonUpState == LOW) {
    sendEspNowMessage("up");
  } else if (currentButtonDownState == LOW) {
    sendEspNowMessage("down");
  } else {
    sendEspNowMessage("hold");
  }

  delay(20); 
}