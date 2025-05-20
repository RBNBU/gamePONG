#include <esp_now.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <secrets.h>

const char* ssid = SECRET_SSID;
const char* password = SECRET_PASSWORD;

const char* mqtt_server = "192.168.0.157";
const int mqtt_port = 1883;
const char* mqtt_topic = "game/Ruben";
const char* mqtt_client_id = "espNow-to-MQTT-bridge";

WiFiClient espClient;
PubSubClient client(espClient);

#define MAX_MSG_LEN 32
char receivedMessage[MAX_MSG_LEN];
volatile bool newData = false;

void OnDataRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len) {

  if (len > 0 && len < MAX_MSG_LEN) {
    memcpy(receivedMessage, incomingData, len);
    receivedMessage[len] = '\0';
    newData = true;

    Serial.print("ESP-NOW Bytes received: ");
    Serial.println(len);
    Serial.print("Message: ");
    Serial.println(receivedMessage);
  } else if (len >= MAX_MSG_LEN) {
    Serial.println("Received message too long for buffer.");
  }
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(mqtt_client_id)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; 
  }
  Serial.println("Serial Initialized.");

  setup_wifi(); 

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  Serial.println("ESP-NOW Initialized.");

  esp_now_register_recv_cb(OnDataRecv);

  client.setServer(mqtt_server, mqtt_port);

  Serial.println("Setup complete.");
}

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  if (newData) {
    newData = false;

    Serial.print("Publishing to MQTT topic '");
    Serial.print(mqtt_topic);
    Serial.print("': ");
    Serial.println(receivedMessage);

    if (client.publish(mqtt_topic, receivedMessage)) {
      Serial.println("MQTT Publish successful");
    } else {
      Serial.println("MQTT Publish failed");
    }
  }

}