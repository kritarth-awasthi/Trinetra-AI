/*
 * display_handler.h — OLED HUD Display Handler.
 * Compatible with SSD1306 128x64 I2C display (most common small OLED).
 * Swap Adafruit_SSD1306 for your display library if using different hardware.
 */
#pragma once
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "camera_config.h"

#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
#define OLED_RESET     -1
#define OLED_ADDRESS 0x3C

// Matches HelmetMode enum from main sketch
enum DisplayMode { DISP_NORMAL, DISP_NIGHT, DISP_IDENTIFY };

class DisplayHandler {
public:
  DisplayHandler() : _display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET) {}

  void begin() {
    Wire.begin(DISPLAY_SDA_PIN, DISPLAY_SCL_PIN);
    if (!_display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
      Serial.println(F("[HUD] Display not found — check wiring/address"));
      _available = false;
      return;
    }
    _available = true;
    _display.clearDisplay();
    _display.setTextColor(SSD1306_WHITE);
    _display.setTextSize(1);
    drawLogo();
  }

  void showStatus(const String& status) {
    if (!_available) return;
    _display.clearDisplay();
    _display.setCursor(0, 0);
    _display.setTextSize(1);
    _display.println("== TRINETRA AI ==");
    _display.println();
    _display.setTextSize(1);
    _display.println(status);
    _display.display();
  }

  void showIP(const String& ip) {
    if (!_available) return;
    _display.clearDisplay();
    _display.setCursor(0, 0);
    _display.println("== TRINETRA AI ==");
    _display.println("Stream ready:");
    _display.println(ip + ":81");
    _display.println("Mode: NORMAL");
    _display.display();
  }

  void showMode(const String& mode) {
    if (!_available) return;
    _currentMode = mode;
    refreshDisplay();
  }

  // Called from loop() — updates HUD with current state
  void update(int mode, bool bleConnected) {
    if (!_available) return;
    unsigned long now = millis();
    if (now - _lastUpdate < 500) return;  // Refresh every 500ms
    _lastUpdate = now;

    _display.clearDisplay();
    _display.setCursor(0, 0);
    _display.setTextSize(1);
    _display.println("=  TRINETRA AI  =");

    _display.print("Mode: ");
    switch (mode) {
      case 0: _display.println("NORMAL");     break;
      case 1: _display.println("NIGHT VISION"); break;
      case 2: _display.println("IDENTIFY");   break;
    }

    _display.print("App: ");
    _display.println(bleConnected ? "CONNECTED" : "WAITING...");

    // Uptime counter
    _display.print("Up: ");
    _display.print(now / 60000);
    _display.println("m");

    _display.display();
  }

private:
  Adafruit_SSD1306 _display;
  bool             _available  = false;
  String           _currentMode = "NORMAL";
  unsigned long    _lastUpdate  = 0;

  void drawLogo() {
    _display.clearDisplay();
    _display.setTextSize(2);
    _display.setCursor(10, 10);
    _display.println("TRINETRA");
    _display.setTextSize(1);
    _display.setCursor(25, 35);
    _display.println("Smart Helmet");
    _display.display();
    delay(1500);
  }

  void refreshDisplay() {
    _display.clearDisplay();
    _display.setCursor(0, 0);
    _display.println("=  TRINETRA AI  =");
    _display.println(_currentMode);
    _display.display();
  }
};
