/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║                   T R I N E T R A   A I                      ║
 * ║                Smart Helmet — ESP32-CAM Firmware             ║
 * ║                                                              ║
 * ║  Developer : Kritarth Awasthi                                ║
 * ║  Hardware  : AI-Thinker ESP32-CAM + SSD1306 OLED             ║
 * ║  Role      : MJPEG video stream + OLED HUD + BLE server      ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 *  SYSTEM FLOW:
 *  ESP32-CAM captures frames → streams MJPEG over WiFi HTTP
 *  Python laptop pipeline reads stream → processes (face detect,
 *  night vision, voice) → sends HUD data back via HTTP POST
 *  ESP32 displays HUD data on SSD1306 OLED
 *  Kotlin Android app connects via BLE for remote control
 */

#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "camera_config.h"

//  WiFi Credentials
#define WIFI_SSID     "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"

// OLED Display 
#define OLED_WIDTH    128
#define OLED_HEIGHT    64
#define OLED_RESET     -1
#define OLED_SDA       15   // Adjust to your wiring
#define OLED_SCL       14
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);

//  BLE UUIDs 
#define BLE_SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define BLE_COMMAND_CHAR_UUID   "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define BLE_STATUS_CHAR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a9"

//  Global State 
bool        nightModeActive  = false;
bool        bleConnected     = false;
String      lastDetection    = "No face";
String      activeMode       = "NORMAL";
httpd_handle_t camera_httpd  = NULL;

BLECharacteristic* pStatusCharacteristic = nullptr;

// HTTP Stream Handler 
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* STREAM_CONTENT_TYPE =
  "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY =
  "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART =
  "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res   = ESP_OK;
  char part_buf[64];

  res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println(F("[CAM] Frame capture failed"));
      res = ESP_FAIL;
      break;
    }

    size_t hlen = snprintf(part_buf, 64, STREAM_PART, fb->len);
    res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
    res = httpd_resp_send_chunk(req, part_buf, hlen);
    res = httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);

    esp_camera_fb_return(fb);
    if (res != ESP_OK) break;
  }
  return res;
}

//  HUD Update Handler (receives data from Python pipeline) 
esp_err_t hud_update_handler(httpd_req_t *req) {
  char buf[256];
  int  ret = httpd_req_recv(req, buf, sizeof(buf) - 1);
  if (ret <= 0) return ESP_FAIL;
  buf[ret] = '\0';

  // Parse simple key=value from Python
  String body = String(buf);
  if (body.indexOf("detection=") != -1) {
    lastDetection = body.substring(body.indexOf("detection=") + 10);
    lastDetection.trim();
  }
  if (body.indexOf("mode=") != -1) {
    activeMode = body.substring(body.indexOf("mode=") + 5);
    activeMode.trim();
    nightModeActive = (activeMode == "NIGHT");
  }

  updateOLED();
  notifyBLE();

  httpd_resp_send(req, "OK", 2);
  return ESP_OK;
}

// Start HTTP Server 
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port    = 80;

  httpd_uri_t stream_uri = {
    .uri      = "/stream",
    .method   = HTTP_GET,
    .handler  = stream_handler,
    .user_ctx = NULL
  };

  httpd_uri_t hud_uri = {
    .uri      = "/hud",
    .method   = HTTP_POST,
    .handler  = hud_update_handler,
    .user_ctx = NULL
  };

  if (httpd_start(&camera_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(camera_httpd, &stream_uri);
    httpd_register_uri_handler(camera_httpd, &hud_uri);
    Serial.println(F("[HTTP] Server started............"));
  }
}

//  OLED HUD Display
void updateOLED() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  // Header
  display.setCursor(0, 0);
  display.println(F("[ TRINETRA AI ]"));
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

  // Mode
  display.setCursor(0, 14);
  display.print(F("Mode: "));
  display.println(activeMode);

  // Detection result
  display.setCursor(0, 26);
  display.print(F("Detected:"));
  display.setCursor(0, 36);
  display.println(lastDetection.substring(0, 20));  // Truncate for display

  // BLE status
  display.setCursor(0, 52);
  display.print(F("BLE: "));
  display.println(bleConnected ? F("Connected") : F("Waiting..."));

  display.display();
}

//  BLE Callbacks 
class TrinetraBLECallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    bleConnected = true;
    Serial.println(F("[BLE] App connected............."));
    updateOLED();
  }
  void onDisconnect(BLEServer* pServer) {
    bleConnected = false;
    Serial.println(F("[BLE] App disconnected!!!!!!!!!!!!!"));
    BLEDevice::startAdvertising();
    updateOLED();
  }
};

class CommandCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pChar) {
    String cmd = pChar->getValue().c_str();
    Serial.printf("[BLE] Command: %s\n", cmd.c_str());

    if      (cmd == "NIGHT_ON")  { nightModeActive = true;  activeMode = "NIGHT"; }
    else if (cmd == "NIGHT_OFF") { nightModeActive = false; activeMode = "NORMAL"; }
    else if (cmd == "CAPTURE")   { Serial.println(F("[CMD] Capture triggered")); }

    updateOLED();
  }
};

void notifyBLE() {
  if (bleConnected && pStatusCharacteristic) {
    String status = "mode=" + activeMode + ",det=" + lastDetection;
    pStatusCharacteristic->setValue(status.c_str());
    pStatusCharacteristic->notify();
  }
}

//  BLE Initialisation
void initBLE() {
  BLEDevice::init("Trinetra-AI");
  BLEServer* pServer = BLEDevice::createServer();
  pServer->setCallbacks(new TrinetraBLECallbacks());

  BLEService* pService = pServer->createService(BLE_SERVICE_UUID);

  BLECharacteristic* pCommandChar = pService->createCharacteristic(
    BLE_COMMAND_CHAR_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  pCommandChar->setCallbacks(new CommandCallbacks());

  pStatusCharacteristic = pService->createCharacteristic(
    BLE_STATUS_CHAR_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pStatusCharacteristic->addDescriptor(new BLE2902());

  pService->start();
  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(BLE_SERVICE_UUID);
  pAdvertising->start();
  Serial.println(F("[BLE] Advertising as 'Trinetra-AI'"));
}


void setup() {
  Serial.begin(115200);
  Serial.println(F("\n[TRINETRA] Booting..."));

  // OLED init
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("[OLED] Init failed"));
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(20, 28);
    display.println(F("TRINETRA BOOTING"));
    display.display();
  }

  // Camera init
  camera_config_t config;
  configureCameraHardware(config);  // from camera_config.h
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] Init failed: 0x%x\n", err);
    return;
  }
  Serial.println(F("[CAM] Ready"));

  // WiFi connect
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print(F("[WiFi] Connecting"));
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\n[WiFi] Connected: http://%s/stream\n",
                WiFi.localIP().toString().c_str());

  startCameraServer();
  initBLE();
  updateOLED();

  Serial.println(F("[TRINETRA] Boot complete"));
}

void loop() {
  delay(10);  // HTTP server runs on FreeRTOS task — loop stays clear
}
