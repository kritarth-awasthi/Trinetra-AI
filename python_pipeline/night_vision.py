"""
night_vision.py — Night Vision Image Enhancement Module

Uses CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance
visibility in low-light conditions. CLAHE operates on the luminance channel
of the LAB colour space, preserving natural colour tones while boosting
local contrast — more effective than global histogram equalisation.
"""

import cv2
import numpy as np


class NightVisionProcessor:
    def __init__(self, clip_limit: float = 3.0, tile_grid: tuple = (8, 8)):
        """
        Args:
            clip_limit : CLAHE contrast limit — higher = more aggressive enhancement
            tile_grid  : Grid size for local histogram computation
        """
        self.clahe = cv2.createCLAHE(
            clipLimit    = clip_limit,
            tileGridSize = tile_grid
        )

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE-based night vision enhancement to a BGR frame.

        Pipeline:
          BGR → LAB colour space
          Extract L (luminance) channel
          Apply CLAHE to L channel only (preserves colour)
          Merge back → LAB → BGR
          Apply green tint for traditional night-vision aesthetic

        Returns:
            Enhanced BGR frame
        """
        # Convert to LAB colour space
        lab   = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # CLAHE on luminance channel only
        l_enhanced = self.clahe.apply(l)

        # Merge enhanced L back with original A, B
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        enhanced     = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        # Apply classic night-vision green tint
        enhanced = self._apply_green_tint(enhanced)

        return enhanced

    def _apply_green_tint(self, frame: np.ndarray) -> np.ndarray:
        """Apply phosphor-green night vision tint."""
        b, g, r = cv2.split(frame)
        # Suppress red and blue, boost green channel
        r_tinted = cv2.multiply(r, 0.3)
        g_tinted = cv2.multiply(g, 1.2)
        b_tinted = cv2.multiply(b, 0.3)
        return cv2.merge([
            b_tinted.astype(np.uint8),
            g_tinted.astype(np.uint8),
            r_tinted.astype(np.uint8)
        ])
