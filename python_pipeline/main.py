"""
╔══════════════════════════════════════════════════════════════╗
║                   T R I N E T R A   A I                      ║
║              Smart Helmet — Python Processing Pipeline       ║
║                                                              ║
║  Developer : Kritarth Awasthi                                ║
║  Runs on   : Laptop connected to ESP32-CAM via WiFi          ║
╚══════════════════════════════════════════════════════════════╝

Pipeline:
  1. Connect to ESP32-CAM MJPEG stream
  2. Feed each frame through face_detector → night_vision → hud_overlay
  3. Listen for voice commands in a background thread
  4. Send HUD data back to ESP32 for OLED display
  5. Display processed feed on laptop screen

Usage:
  python main.py --ip 192.168.1.100 --port 80
"""

import cv2
import requests
import threading
import argparse
import numpy as np
import time
from face_detector   import FaceDetector
from night_vision    import NightVisionProcessor
from voice_commander import VoiceCommander
from hud_overlay     import HUDOverlay

# ── Configuration 
ESP32_IP         = "192.168.1.100"   # Change to your ESP32-CAM IP
ESP32_PORT       = 80
STREAM_URL       = f"http://{ESP32_IP}:{ESP32_PORT}/stream"
HUD_UPDATE_URL   = f"http://{ESP32_IP}:{ESP32_PORT}/hud"
HUD_UPDATE_INTERVAL = 0.5            # Send HUD update to ESP32 every 0.5s

# ── Global State 
night_mode_active  = False
current_detection  = "Scanning..."
last_hud_update    = 0
running            = True


def send_hud_update(detection: str, mode: str):
    """Push detection result and mode to ESP32 OLED display."""
    try:
        payload = f"detection={detection}&mode={mode}"
        requests.post(HUD_UPDATE_URL, data=payload, timeout=1)
    except requests.exceptions.RequestException:
        pass  # Non-blocking — OLED update failure doesn't stop pipeline


def on_voice_command(command: str):
    """Callback fired by VoiceCommander on keyword detection."""
    global night_mode_active, current_detection
    print(f"[VOICE] Command: {command}")

    if command == "night mode":
        night_mode_active = True
        print("[MODE] Night vision ON")
    elif command == "normal mode":
        night_mode_active = False
        print("[MODE] Night vision OFF")
    elif command == "identify":
        print("[CMD] Force identify triggered")
    elif command == "capture":
        timestamp = int(time.time())
        cv2.imwrite(f"capture_{timestamp}.jpg", current_frame)
        print(f"[CMD] Frame saved as capture_{timestamp}.jpg")
    elif command == "stop":
        global running
        running = False
        print("[CMD] Stopping pipeline........")


def main():
    global night_mode_active, current_detection, last_hud_update
    global current_frame

    parser = argparse.ArgumentParser(description="Trinetra AI Pipeline")
    parser.add_argument("--ip",   default=ESP32_IP,   help="ESP32-CAM IP address")
    parser.add_argument("--port", default=ESP32_PORT,  type=int, help="ESP32-CAM port")
    args = parser.parse_args()

    stream_url = f"http://{args.ip}:{args.port}/stream"
    hud_url    = f"http://{args.ip}:{args.port}/hud"

    # Initialise modules
    face_detector  = FaceDetector()
    night_vision   = NightVisionProcessor()
    hud            = HUDOverlay()
    voice          = VoiceCommander(callback=on_voice_command)

    # Start voice command listener in background thread
    voice_thread = threading.Thread(target=voice.listen, daemon=True)
    voice_thread.start()
    print("[VOICE] Listener started in background")

    # Connect to ESP32-CAM stream
    print(f"[STREAM] Connecting to {stream_url}")
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("[ERROR] Cannot connect to ESP32-CAM stream")
        print("        Ensure ESP32-CAM is powered and on same WiFi network")
        return

    print("[STREAM] Connected. Pipeline running.")
    print("         Press 'q' to quit | 'n' to toggle night mode | 'c' to capture")

    fps_counter = 0
    fps_timer   = time.time()
    fps         = 0

    while running:
        ret, frame = cap.read()
        if not ret:
            print("[STREAM] Frame read failed — reconnecting...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(stream_url)
            continue

        current_frame = frame.copy()

        # Apply night vision if active
        if night_mode_active:
            frame = night_vision.process(frame)
            mode_label = "NIGHT"
        else:
            mode_label = "NORMAL"

        # Run face detection
        faces, labels = face_detector.detect(frame)
        if faces:
            current_detection = labels[0] if labels else "Unknown"
        else:
            current_detection = "No face"

        # Draw HUD overlay
        frame = hud.draw(
            frame      = frame,
            faces      = faces,
            labels     = labels,
            mode       = mode_label,
            fps        = fps,
            voice_hint = voice.last_command
        )

        # Send HUD data to ESP32 OLED periodically
        if time.time() - last_hud_update > HUD_UPDATE_INTERVAL:
            threading.Thread(
                target=send_hud_update,
                args=(current_detection, mode_label),
                daemon=True
            ).start()
            last_hud_update = time.time()

        # FPS calculation
        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            fps         = fps_counter
            fps_counter = 0
            fps_timer   = time.time()

        cv2.imshow("Trinetra AI — Helmet Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if   key == ord('q'): break
        elif key == ord('n'): night_mode_active = not night_mode_active
        elif key == ord('c'):
            timestamp = int(time.time())
            cv2.imwrite(f"capture_{timestamp}.jpg", frame)
            print(f"[CAPTURE] Saved capture_{timestamp}.jpg")

    cap.release()
    cv2.destroyAllWindows()
    print("[TRINETRA] Pipeline stopped.")


if __name__ == "__main__":
    main()
