#include <esp_now.h>
#include <WiFi.h>

uint8_t gatewayAddress[] = {0x1C, 0x69, 0x20, 0xCC, 0xD5, 0xBC};

const int buttonUpPin = 2;
const int buttonDownPin = 4;

esp_now_peer_info_t peerInfo;

int lastRawButtonUpState = HIGH;
int lastRawButtonDownState = HIGH;
int currentDebouncedButtonUpState = HIGH;
int currentDebouncedButtonDownState = HIGH;

String lastMessageActuallySent = "";
unsigned long lastDebounceTimeUp = 0;
unsigned long lastDebounceTimeDown = 0;
unsigned long debounceDelay = 50;

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("\r\nESP-NOW Send Status to ");
  for (int i = 0; i < 6; i++) {
    Serial.print(mac_addr[i], HEX);
    if (i < 5) Serial.print(":");
  }
  Serial.print(" : ");
  if (status == ESP_NOW_SEND_SUCCESS) {
    Serial.println("Delivery success");
  } else {
    Serial.println("Delivery fail");
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }
  Serial.println("\nESP32 ESP-NOW Button Sender");

  WiFi.mode(WIFI_STA);
  Serial.print("This ESP32 (Sender) MAC Address: ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    while (1) delay(1000);
  }
  Serial.println("ESP-NOW Initialized.");

  esp_now_register_send_cb(OnDataSent);

  memcpy(peerInfo.peer_addr, gatewayAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    while (1) delay(1000);
  }
  Serial.println("Peer (Gateway) Added.");

  pinMode(buttonUpPin, INPUT_PULLUP);
  pinMode(buttonDownPin, INPUT_PULLUP);

  lastRawButtonUpState = digitalRead(buttonUpPin);
  lastRawButtonDownState = digitalRead(buttonDownPin);
  currentDebouncedButtonUpState = lastRawButtonUpState;
  currentDebouncedButtonDownState = lastRawButtonDownState;

  if (currentDebouncedButtonUpState == LOW) {
    lastMessageActuallySent = "up";
  } else if (currentDebouncedButtonDownState == LOW) {
    lastMessageActuallySent = "down";
  } else {
    lastMessageActuallySent = "hold";
  }
  esp_err_t result = esp_now_send(gatewayAddress, (uint8_t *)lastMessageActuallySent.c_str(), lastMessageActuallySent.length());
  if (result == ESP_OK) {
    Serial.print("Initial state sent: ");
    Serial.println(lastMessageActuallySent);
  } else {
    Serial.print("Error sending initial state: ");
    Serial.println(lastMessageActuallySent);
  }


  Serial.println("Setup complete. Monitoring buttons.");
}

void loop() {
  int readingUp = digitalRead(buttonUpPin);

  if (readingUp != lastRawButtonUpState) {
    lastDebounceTimeUp = millis();
  }

  if ((millis() - lastDebounceTimeUp) > debounceDelay) {
    if (readingUp != currentDebouncedButtonUpState) {
      currentDebouncedButtonUpState = readingUp;
    }
  }
  lastRawButtonUpState = readingUp;

  int readingDown = digitalRead(buttonDownPin);

  if (readingDown != lastRawButtonDownState) {
    lastDebounceTimeDown = millis();
  }

  if ((millis() - lastDebounceTimeDown) > debounceDelay) {
    if (readingDown != currentDebouncedButtonDownState) {
      currentDebouncedButtonDownState = readingDown;
    }
  }
  lastRawButtonDownState = readingDown;

  String messageToSend = "";
  if (currentDebouncedButtonUpState == LOW) {
    messageToSend = "up";
  } else if (currentDebouncedButtonDownState == LOW) {
    messageToSend = "down";
  } else {
    messageToSend = "hold";
  }

  if (messageToSend != lastMessageActuallySent) {
    esp_err_t result = esp_now_send(gatewayAddress, (uint8_t *)messageToSend.c_str(), messageToSend.length());

    if (result == ESP_OK) {
      Serial.print("Sent message due to state change: ");
      Serial.println(messageToSend);
      lastMessageActuallySent = messageToSend;
    } else {
      Serial.print("Error sending message '");
      Serial.print(messageToSend);
      Serial.print("'. ESP-NOW Error Code: ");
      Serial.println(result);
    }
  }
  delay(20);
}