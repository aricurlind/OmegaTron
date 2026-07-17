"""Klassische (nicht-DL-basierte) Fahrspurerkennung über HSV-Filter und Histogramme."""

from collections import deque
from typing import Deque

import cv2
import numpy as np

import Hilfsfunktionen

CURVE_SMOOTHING_WINDOW: int = 10
CURVE_NORMALIZATION: float = 100.0

_curve_history: Deque[float] = deque(maxlen=CURVE_SMOOTHING_WINDOW)


def getLaneCurve(img: np.ndarray, display: int = 2) -> float:
    """Berechnet den normierten Lenkwert aus dem aktuellen Kamerabild.

    :param img: BGR-Kamerabild.
    :param display: 0 = keine Visualisierung, sonst wird das Ergebnis eingezeichnet.
    :return: Lenkwert im Bereich [-1.0, 1.0]; negativ = links, positiv = rechts.
    """
    img_threshold = Hilfsfunktionen.Grenzwerte(img)

    hT, wT, _ = img.shape
    points = Hilfsfunktionen.valTrackbars()
    img_warp = Hilfsfunktionen.warpImg(img_threshold, points, wT, hT)

    img_warp_points = Hilfsfunktionen.drawPoints(img.copy(), points)

    mittelpunkt, img_hist = Hilfsfunktionen.getHistogram(img_warp, display=True, minPer=0.5, region=4)
    kurven_mittelwert, img_hist = Hilfsfunktionen.getHistogram(img_warp, display=True, minPer=0.9)
    curve_raw = kurven_mittelwert - mittelpunkt

    _curve_history.append(curve_raw)
    curve = int(sum(_curve_history) / len(_curve_history))

    if display != 0:
        img_result = img.copy()
        img_inv_warp = Hilfsfunktionen.warpImg(img_warp, points, wT, hT, inv=True)
        img_inv_warp = cv2.cvtColor(img_inv_warp, cv2.COLOR_GRAY2BGR)
        img_inv_warp[0:hT // 3, 0:wT] = (0, 0, 0)
        img_lane_color = np.zeros_like(img)
        img_lane_color[:] = (0, 255, 0)
        img_lane_color = cv2.bitwise_and(img_inv_warp, img_lane_color)
        img_result = cv2.addWeighted(img_result, 1, img_lane_color, 1, 0)

        mid_y = 450
        cv2.putText(img_result, str(curve), (wT // 2 - 80, 85), cv2.FONT_HERSHEY_COMPLEX, 2, (255, 0, 255), 3)
        cv2.line(img_result, (wT // 2, mid_y), (wT // 2 + (curve * 3), mid_y), (255, 0, 255), 5)
        cv2.line(img_result, (wT // 2 + (curve * 3), mid_y - 25), (wT // 2 + (curve * 3), mid_y + 25), (0, 255, 0), 5)
        for x in range(-30, 30):
            w = wT // 20
            cv2.line(img_result, (w * x + int(curve // 50), mid_y - 10),
                     (w * x + int(curve // 50), mid_y + 10), (0, 0, 255), 2)

    normalized_curve = curve / CURVE_NORMALIZATION
    return max(-1.0, min(1.0, normalized_curve))


if __name__ == "__main__":
    cap = cv2.VideoCapture("Vid1.mp4")
    initial_trackbar_vals = [102, 80, 20, 214]
    Hilfsfunktionen.initializeTrackbars(initial_trackbar_vals)

    frame_counter = 0
    while True:
        frame_counter += 1
        if cap.get(cv2.CAP_PROP_FRAME_COUNT) == frame_counter:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_counter = 0

        success, img = cap.read()
        if not success:
            break

        curve = getLaneCurve(img, display=2)
        print(curve)
        cv2.imshow("Video_Fahrspurerkennung", img)
        cv2.waitKey(1)
