#include <WiFi.h>
#include <esp_now.h>
#include <PubSubClient.h>
#include <secrets.h>

const char* ssid = SECRET_SSID;
const char* password = SECRET_PASSWORD; 

const char* mqttServerIp = "192.168.0.157";
const int mqttPort = 1883;
const char* mqttTopic = "game/Ruben";
const char* mqttClientIdBase = "esp32-pong-bridge";

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

void OnDataRecv(const esp_now_recv_info_t *esp_now_info, const uint8_t *incomingData, int len) {
  Serial.print("ESP-NOW Packet from: ");
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
           esp_now_info->src_addr[0], esp_now_info->src_addr[1], esp_now_info->src_addr[2],
           esp_now_info->src_addr[3], esp_now_info->src_addr[4], esp_now_info->src_addr[5]);
  Serial.print(macStr);

  char dataBuffer[len + 1];
  memcpy(dataBuffer, incomingData, len);
  dataBuffer[len] = '\0';

  Serial.print(" | Data: ");
  Serial.print(dataBuffer);

  if (mqttClient.connected()) {
    if (mqttClient.publish(mqttTopic, dataBuffer)) {
      Serial.println(" | Published to MQTT");
    } else {
      Serial.println(" | MQTT Publish Failed!");
    }
  } else {
    Serial.println(" | MQTT Not Connected - Cannot Publish.");
  }
}

void setupMQTT() {
  mqttClient.setServer(mqttServerIp, mqttPort);
  String clientId = mqttClientIdBase + String(random(0xffff), HEX);
  Serial.print("Attempting MQTT connection with Client ID: ");
  Serial.println(clientId);
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = mqttClientIdBase + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected to MQTT Broker!");

    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\nESP32 ESP-NOW to MQTT Gateway");

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int wifi_retry_count = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    wifi_retry_count++;
    if (wifi_retry_count > 20) {
        Serial.println("\nFailed to connect to WiFi. Please check credentials or network.");
        ESP.restart(); 
    }
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  setupMQTT();
    if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  esp_now_register_recv_cb(OnDataRecv);
  Serial.println("ESP-NOW Initialized. Waiting for data...");
  Serial.print("This ESP32's MAC Address (for sender config): ");
  Serial.println(WiFi.macAddress());
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  delay(10);
}