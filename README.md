# Trinetra AI — Smart Helmet

> Real-time computer vision system integrated into a wearable helmet.
> CLAHE night vision · Haarcascade face detection · Voice commands · BLE control

**Developer:** Kritarth Awasthi 

**Status:** Prototype complete

---

## What it does

A wearable smart helmet that streams live video from an ESP32-CAM to a
connected laptop, where a Python pipeline performs real-time face detection,
night vision enhancement, and voice command recognition. Processed HUD data
is sent back to an OLED display mounted on the helmet. A Kotlin Android app
provides BLE-based remote control.

---

## Architecture

```
ESP32-CAM (helmet) → MJPEG WiFi stream → Python laptop pipeline
                                         ├── Haarcascade face detection
                                         ├── CLAHE night vision
                                         ├── SpeechRecognition keywords
                                         └── HUD overlay on screen
                   ← HTTP POST /hud ────── OLED display update
Android App ←──── BLE notify ──────────── Status + detections
Android App ──────BLE write ──────────── NIGHT_ON / CAPTURE / etc.
```

---

## Hardware

| Component | Model | Role |
|---|---|---|
| Camera + MCU | AI-Thinker ESP32-CAM | Video capture + BLE server |
| Helmet Display | SSD1306 OLED 128x64 | HUD data display |
| Processing | Laptop (Python) | CV pipeline |
| App | Android (Kotlin) | BLE remote control |

---

## Python Pipeline

```bash
pip install -r python_pipeline/requirements.txt
python python_pipeline/main.py --ip 192.168.1.100
```

**Controls:**
- `n` → toggle night mode
- `c` → capture frame
- `q` → quit
- Voice: *"night mode"*, *"identify"*, *"capture"*, *"stop"*

---

## Night Vision — Why CLAHE

Standard approaches either convert to grayscale (losing colour) or apply
global histogram equalisation (overexposes bright areas). CLAHE operates on
the luminance channel of the LAB colour space in 8×8 local tiles — boosting
dark region contrast without blowing out lit areas. Green phosphor tint applied
for traditional night-vision aesthetic.

---

## ESP32 Firmware

Open `esp32_firmware/trinetra_esp32cam/trinetra_esp32cam.ino` in Arduino IDE.

Required libraries (install via Library Manager):
- Adafruit SSD1306.
- Adafruit GFX Library.
- ESP32 BLE Arduino.

Update `WIFI_SSID` and `WIFI_PASSWORD` in the `.ino` file before flashing.

---

## Roadmap

- [ ] YOLOv8 object detection.
- [ ] DeepFace recognition (replace LBPH).
- [ ] Offline voice commands (Whisper — remove Google API).
- [ ] Migrate processing to Raspberry Pi (on-helmet)
- [ ] Real-time video stream inside Android app

---
*Kritarth Awasthi | BIT Mesra, Jaipur | May–Aug 2025*
