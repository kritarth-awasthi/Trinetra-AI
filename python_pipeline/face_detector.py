"""
face_detector.py — Haarcascade Face Detection Module

Uses OpenCV's built-in Haarcascade classifier for face detection.
LBPH (Local Binary Pattern Histogram) recogniser for face identification
from a pre-trained dataset.

ROADMAP: Replace Haarcascade + LBPH with YOLOv8 face detection model
         for improved accuracy under varying angles and lighting conditions.
"""

import cv2
import numpy as np
import os

# Haarcascade XML path (bundled with OpenCV)
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Path to trained LBPH recogniser model (train with train_faces.py)
RECOGNISER_MODEL_PATH = "models/face_recogniser.yml"
LABELS_PATH           = "models/labels.txt"

# Detection confidence threshold
CONFIDENCE_THRESHOLD  = 80  # Lower = stricter match


class FaceDetector:
    def __init__(self):
        # Load Haarcascade
        self.cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
        if self.cascade.empty():
            raise RuntimeError("Haarcascade XML not found — check OpenCV installation")

        # Load LBPH recogniser if model exists
        self.recogniser = None
        self.labels     = {}
        self._load_recogniser()

    def _load_recogniser(self):
        """Load pre-trained LBPH face recogniser if model file exists."""
        if os.path.exists(RECOGNISER_MODEL_PATH):
            self.recogniser = cv2.face.LBPHFaceRecognizer_create()
            self.recogniser.read(RECOGNISER_MODEL_PATH)

            if os.path.exists(LABELS_PATH):
                with open(LABELS_PATH, "r") as f:
                    for line in f:
                        idx, name = line.strip().split(",")
                        self.labels[int(idx)] = name
            print(f"[FACE] Recogniser loaded — {len(self.labels)} known faces")
        else:
            print("[FACE] No recogniser model found — detection only (no identification)")
            print("       Run train_faces.py to add known faces")

    def detect(self, frame: np.ndarray):
        """
        Detect and optionally identify faces in a frame.

        Returns:
            faces  : list of (x, y, w, h) bounding boxes
            labels : list of name strings (or "Unknown") per face
        """
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Equalise histogram for better detection under varying light
        gray  = cv2.equalizeHist(gray)

        detected = self.cascade.detectMultiScale(
            gray,
            scaleFactor  = 1.1,
            minNeighbors = 5,
            minSize      = (60, 60),
            flags        = cv2.CASCADE_SCALE_IMAGE
        )

        faces  = []
        labels = []

        for (x, y, w, h) in detected:
            faces.append((x, y, w, h))
            face_roi = gray[y:y + h, x:x + w]

            if self.recogniser is not None:
                label_idx, confidence = self.recogniser.predict(face_roi)
                if confidence < CONFIDENCE_THRESHOLD:
                    name = self.labels.get(label_idx, "Unknown")
                else:
                    name = f"Unknown ({int(confidence)})"
            else:
                name = "Face detected"

            labels.append(name)

        return faces, labels
