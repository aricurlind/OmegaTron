"""Bildverarbeitungs-Hilfsfunktionen für die klassische Fahrspurerkennung."""

from typing import List, Tuple

import cv2
import numpy as np

LOWER_WHITE_HSV: Tuple[int, int, int] = (80, 0, 0)
UPPER_WHITE_HSV: Tuple[int, int, int] = (255, 160, 255)


def Grenzwerte(img: np.ndarray) -> np.ndarray:
    """HSV-Schwellwertfilter: konvertiert BGR in HSV und maskiert den Fahrstreifen."""
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_white = np.array(LOWER_WHITE_HSV)
    upper_white = np.array(UPPER_WHITE_HSV)
    return cv2.inRange(img_hsv, lower_white, upper_white)


def warpImg(img: np.ndarray, points: np.ndarray, w: int, h: int, inv: bool = False) -> np.ndarray:
    """Birds-Eye-View-Transformation (perspektivische Entzerrung)."""
    unwarped = np.float32(points)
    warped = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    if inv:
        matrix = cv2.getPerspectiveTransform(warped, unwarped)
    else:
        matrix = cv2.getPerspectiveTransform(unwarped, warped)
    return cv2.warpPerspective(img, matrix, (w, h))


def empty(_a) -> None:
    """Leerer Trackbar-Callback (OpenCV benötigt eine Callback-Funktion)."""


def initializeTrackbars(initial_vals: List[int], wT: int = 480, hT: int = 280) -> None:
    cv2.namedWindow("Trackbars")
    cv2.resizeWindow("Trackbars", 360, 240)
    cv2.createTrackbar("Width Top", "Trackbars", initial_vals[0], wT // 2, empty)
    cv2.createTrackbar("Height Top", "Trackbars", initial_vals[1], hT, empty)
    cv2.createTrackbar("Width Bottom", "Trackbars", initial_vals[2], wT // 2, empty)
    cv2.createTrackbar("Height Bottom", "Trackbars", initial_vals[3], hT, empty)


def valTrackbars(wT: int = 480, hT: int = 240) -> np.ndarray:
    width_top = cv2.getTrackbarPos("Width Top", "Trackbars")
    height_top = cv2.getTrackbarPos("Height Top", "Trackbars")
    width_bottom = cv2.getTrackbarPos("Width Bottom", "Trackbars")
    height_bottom = cv2.getTrackbarPos("Height Bottom", "Trackbars")
    return np.float32([
        (width_top, height_top),
        (wT - width_top, height_top),
        (width_bottom, height_bottom),
        (wT - width_bottom, height_bottom),
    ])


def drawPoints(img: np.ndarray, points: np.ndarray) -> np.ndarray:
    for point in points:
        cv2.circle(img, (int(point[0]), int(point[1])), 15, (0, 0, 255), cv2.FILLED)
    return img


def getHistogram(img: np.ndarray, minPer: float = 0.1, display: bool = False, region: int = 1):
    """Erstellt ein Spaltenhistogramm zur Bestimmung des Fahrspurmittelpunkts."""
    if region == 1:
        hist_values = np.sum(img, axis=0)
    else:
        hist_values = np.sum(img[img.shape[0] // region:, :], axis=0)

    max_value = np.max(hist_values)
    min_value = minPer * max_value
    index_array = np.where(hist_values >= min_value)
    base_point = int(np.average(index_array))

    if display:
        img_hist = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
        for x, intensity in enumerate(hist_values):
            cv2.line(img_hist, (x, img.shape[0]), (x, img.shape[0] - intensity // 255 // region), (255, 0, 255), 1)
        cv2.circle(img_hist, (base_point, img.shape[0]), 20, (0, 255, 255), cv2.FILLED)
        return base_point, img_hist
    return base_point


def stackImages(scale: float, img_array):
    """Stellt mehrere Bildverarbeitungsschritte als Panel-Ansicht dar (Debug-Hilfe)."""
    rows = len(img_array)
    cols = len(img_array[0])
    rows_available = isinstance(img_array[0], list)
    width = img_array[0][0].shape[1] if rows_available else img_array[0].shape[1]
    height = img_array[0][0].shape[0] if rows_available else img_array[0].shape[0]

    if rows_available:
        for x in range(rows):
            for y in range(cols):
                if img_array[x][y].shape[:2] == img_array[0][0].shape[:2]:
                    img_array[x][y] = cv2.resize(img_array[x][y], (0, 0), None, scale, scale)
                else:
                    img_array[x][y] = cv2.resize(
                        img_array[x][y], (img_array[0][0].shape[1], img_array[0][0].shape[0]), None, scale, scale)
                if len(img_array[x][y].shape) == 2:
                    img_array[x][y] = cv2.cvtColor(img_array[x][y], cv2.COLOR_GRAY2BGR)
        image_blank = np.zeros((height, width, 3), np.uint8)
        hor = [image_blank] * rows
        for x in range(rows):
            hor[x] = np.hstack(img_array[x])
        return np.vstack(hor)

    for x in range(rows):
        if img_array[x].shape[:2] == img_array[0].shape[:2]:
            img_array[x] = cv2.resize(img_array[x], (0, 0), None, scale, scale)
        else:
            img_array[x] = cv2.resize(img_array[x], (img_array[0].shape[1], img_array[0].shape[0]), None, scale, scale)
        if len(img_array[x].shape) == 2:
            img_array[x] = cv2.cvtColor(img_array[x], cv2.COLOR_GRAY2BGR)
    return np.hstack(img_array)
