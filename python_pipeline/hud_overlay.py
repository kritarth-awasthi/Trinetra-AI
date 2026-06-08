"""
hud_overlay.py — AR HUD Overlay Renderer

Draws helmet-style augmented reality overlay on the video feed
displayed on the laptop screen. Includes face detection boxes,
identification labels, mode indicator, FPS counter, and voice
command feedback.
"""

import cv2
import numpy as np
import time


# HUD Colour Palette (BGR)
HUD_GREEN      = (0,   255, 0)
HUD_RED        = (0,   0,   255)
HUD_CYAN       = (255, 255, 0)
HUD_WHITE      = (255, 255, 255)
HUD_DARK       = (0,   50,  0)
HUD_NIGHT_TINT = (0,   200, 0)


class HUDOverlay:
    def __init__(self):
        self.font       = cv2.FONT_HERSHEY_SIMPLEX
        self.font_small = 0.45
        self.font_med   = 0.6
        self.thickness  = 1

    def draw(self, frame, faces, labels, mode, fps, voice_hint=""):
        """
        Draw complete HUD overlay on frame.

        Args:
            frame      : BGR numpy array from pipeline
            faces      : list of (x, y, w, h) face bounding boxes
            labels     : list of name strings per face
            mode       : "NORMAL" or "NIGHT"
            fps        : current frames per second
            voice_hint : last voice command received

        Returns:
            Annotated BGR frame
        """
        h, w = frame.shape[:2]
        overlay = frame.copy()

        # ── Corner brackets (helmet visor aesthetic) ─────────────────────────
        bracket_len = 20
        bracket_col = HUD_GREEN if mode == "NORMAL" else HUD_NIGHT_TINT
        self._draw_corner_brackets(overlay, w, h, bracket_len, bracket_col)

        # ── Mode indicator (top left) ─────────────────────────────────────────
        mode_text = f"[ {mode} MODE ]"
        mode_col  = HUD_GREEN if mode == "NORMAL" else HUD_NIGHT_TINT
        cv2.putText(overlay, mode_text, (10, 20),
                    self.font, self.font_small, mode_col, self.thickness)

        # ── FPS counter (top right) ───────────────────────────────────────────
        fps_text = f"FPS: {fps}"
        fps_x    = w - 90
        cv2.putText(overlay, fps_text, (fps_x, 20),
                    self.font, self.font_small, HUD_CYAN, self.thickness)

        # ── System label (bottom left) ────────────────────────────────────────
        cv2.putText(overlay, "TRINETRA AI v1.0", (10, h - 10),
                    self.font, self.font_small, HUD_CYAN, self.thickness)

        # ── Voice command feedback (bottom right) ─────────────────────────────
        if voice_hint:
            cmd_text = f"CMD: {voice_hint.upper()}"
            cmd_x    = w - len(cmd_text) * 8
            cv2.putText(overlay, cmd_text, (cmd_x, h - 10),
                        self.font, self.font_small, HUD_WHITE, self.thickness)

        # ── Face detection boxes and labels ───────────────────────────────────
        for i, (x, y, fw, fh) in enumerate(faces):
            label = labels[i] if i < len(labels) else "Unknown"
            is_known = "Unknown" not in label

            box_col   = HUD_GREEN if is_known else HUD_RED
            label_col = HUD_GREEN if is_known else HUD_RED

            # Tactical-style face box with corner brackets
            self._draw_tactical_box(overlay, x, y, fw, fh, box_col)

            # Label above box
            label_text = label.upper()
            label_y    = y - 8 if y - 8 > 10 else y + fh + 16
            cv2.putText(overlay, label_text, (x, label_y),
                        self.font, self.font_small, label_col, self.thickness)

            # Confidence bar below box
            if "(" in label:
                try:
                    conf = int(label.split("(")[1].replace(")", ""))
                    bar_width = int((1 - conf / 100) * fw)
                    cv2.rectangle(overlay, (x, y + fh + 2),
                                  (x + bar_width, y + fh + 6), box_col, -1)
                except ValueError:
                    pass

        # ── Scanning animation (when no faces) ───────────────────────────────
        if not faces:
            cx, cy   = w // 2, h // 2
            scan_rad = 40
            cv2.circle(overlay, (cx, cy), scan_rad, HUD_GREEN, 1)
            cv2.putText(overlay, "SCANNING...", (cx - 45, cy + scan_rad + 16),
                        self.font, self.font_small, HUD_GREEN, self.thickness)

        # Blend overlay with original for subtle transparency effect
        result = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        return result

    def _draw_corner_brackets(self, frame, w, h, length, color):
        """Draw four corner L-brackets for visor aesthetic."""
        t = self.thickness + 1
        # Top-left
        cv2.line(frame, (5, 5),        (5 + length, 5),      color, t)
        cv2.line(frame, (5, 5),        (5, 5 + length),       color, t)
        # Top-right
        cv2.line(frame, (w - 5, 5),    (w - 5 - length, 5),  color, t)
        cv2.line(frame, (w - 5, 5),    (w - 5, 5 + length),  color, t)
        # Bottom-left
        cv2.line(frame, (5, h - 5),    (5 + length, h - 5),  color, t)
        cv2.line(frame, (5, h - 5),    (5, h - 5 - length),  color, t)
        # Bottom-right
        cv2.line(frame, (w-5, h-5),    (w-5-length, h-5),    color, t)
        cv2.line(frame, (w-5, h-5),    (w-5, h-5-length),    color, t)

    def _draw_tactical_box(self, frame, x, y, w, h, color):
        """Draw corner-bracket style box instead of full rectangle."""
        length = min(w, h) // 4
        t      = self.thickness + 1
        # Top-left
        cv2.line(frame, (x, y),         (x + length, y),         color, t)
        cv2.line(frame, (x, y),         (x, y + length),          color, t)
        # Top-right
        cv2.line(frame, (x + w, y),     (x + w - length, y),     color, t)
        cv2.line(frame, (x + w, y),     (x + w, y + length),     color, t)
        # Bottom-left
        cv2.line(frame, (x, y + h),     (x + length, y + h),     color, t)
        cv2.line(frame, (x, y + h),     (x, y + h - length),     color, t)
        # Bottom-right
        cv2.line(frame, (x + w, y + h), (x + w - length, y + h), color, t)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - length), color, t)
