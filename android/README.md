# Trinetra AI — Android Companion App

## Overview
Built in Kotlin. Connects to the ESP32-CAM via BLE to send
control commands and receive status notifications.

## BLE Communication
- **Service UUID:** 4fafc201-1fb5-459e-8fcc-c5c9c331914b
- **Command Characteristic (WRITE):** Send commands to helmet.
- **Status Characteristic (NOTIFY):** Receive detection results.

## Commands Sent from App
| Command    | Effect                        |
|---|---|
| NIGHT_ON   | Activate night vision mode    |
| NIGHT_OFF  | Return to normal mode         |
| CAPTURE    | Trigger frame capture         |

## Status Received from Helmet
```
mode=NORMAL,det=Kritarth Awasthi
mode=NIGHT,det=No face
```

## Tech Stack
- Kotlin
- Android BLE API (BluetoothLeScanner, BluetoothGatt)
- Android SDK min API 23

## Roadmap
- Live camera feed view inside app (via WiFi HTTP stream)
- Known faces database management
- Voice command trigger from phone
- Helmet battery level indicator
