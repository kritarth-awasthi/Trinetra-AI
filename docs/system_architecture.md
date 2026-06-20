# Trinetra AI — System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      HELMET (Wearable)                      │
│                                                             │
│  ┌──────────────────┐    I2C    ┌──────────────────────┐    │
│  │  ESP32-CAM       │ ────────► │  SSD1306 OLED        │    │
│  │  AI-Thinker      │           │  128x64 HUD display  │    │
│  │                  │           └──────────────────────┘    │
│  │  OV2640 Camera   │                                       │
│  │  WiFi 2.4GHz     │                                       │
│  │  BLE 4.2         │                                       │
│  └────────┬─────────┘                                       │
│           │ WiFi MJPEG stream (HTTP)                        │
└───────────┼─────────────────────────────────────────────────┘
            │
            │  Same WiFi network
            ▼
┌─────────────────────────────────────────────────────────────┐
│                   LAPTOP (Processing)                       │
│                                                             │
│  main.py                                                    │
│  ├── face_detector.py   → Haarcascade + LBPH recognition    │
│  ├── night_vision.py    → CLAHE luminance enhancement       │
│  ├── voice_commander.py → SpeechRecognition keywords        │
│  └── hud_overlay.py     → AR overlay on laptop display      │
│                                                             │
│  HTTP POST /hud → ESP32 OLED update                         │
└─────────────────────────────────────────────────────────────┘
            │
            │  BLE 4.2
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 ANDROID APP (Kotlin)                        │
│  Send commands: NIGHT_ON / NIGHT_OFF / CAPTURE              │
│  Receive status: detection result + active mode             │
└─────────────────────────────────────────────────────────────┘
```

## Night Vision — CLAHE Approach

Standard histogram equalisation operates globally — it stretches the
overall contrast but can overexpose bright regions and miss dark detail.

CLAHE (Contrast Limited Adaptive Histogram Equalization) divides the
image into small tiles (8×8 grid) and equalises each tile independently,
with a contrast clip limit to prevent over-amplification of noise.

Operating on the L channel of LAB colour space preserves natural colours
while boosting luminance — making it more effective than grayscale
conversion or global equalisation.

## Voice Recognition Keywords

| Keyword       | Action                         |
|---|---|
| "night mode"  | Activate CLAHE night vision    |
| "normal mode" | Deactivate night vision        |
| "identify"    | Force face identification pass |
| "capture"     | Save current frame to disk     |
| "stop"        | Shutdown pipeline              |

## Roadmap

- [ ] YOLOv8 object detection (replace basic CV detection).
- [ ] DeepFace recognition (replace LBPH).
- [ ] Offline voice commands via Whisper (remove Google API dependency).
- [ ] Raspberry Pi migration (remove laptop from pipeline).
- [ ] Onboard processing — no external device needed

---
*Kritarth Awasthi | BIT Mesra, Jaipur | May–Aug 2025*
