"""Interaktives Tool zum Einstellen der HSV-Schwellwerte für die Fahrspurerkennung."""

from typing import Tuple

import cv2
import numpy as np

VIDEO_PATH: str = "vid1.mp4"
WINDOW_NAME: str = "HSV"


def empty(_a) -> None:
    """Leerer Trackbar-Callback (OpenCV benötigt eine Callback-Funktion)."""


def create_trackbars() -> None:
    cv2.namedWindow(WINDOW_NAME)
    cv2.resizeWindow(WINDOW_NAME, 640, 240)
    cv2.createTrackbar("HUE Min", WINDOW_NAME, 0, 179, empty)
    cv2.createTrackbar("HUE Max", WINDOW_NAME, 179, 179, empty)
    cv2.createTrackbar("SAT Min", WINDOW_NAME, 0, 255, empty)
    cv2.createTrackbar("SAT Max", WINDOW_NAME, 255, 255, empty)
    cv2.createTrackbar("VALUE Min", WINDOW_NAME, 0, 255, empty)
    cv2.createTrackbar("VALUE Max", WINDOW_NAME, 255, 255, empty)


def read_trackbar_bounds() -> Tuple[np.ndarray, np.ndarray]:
    h_min = cv2.getTrackbarPos("HUE Min", WINDOW_NAME)
    h_max = cv2.getTrackbarPos("HUE Max", WINDOW_NAME)
    s_min = cv2.getTrackbarPos("SAT Min", WINDOW_NAME)
    s_max = cv2.getTrackbarPos("SAT Max", WINDOW_NAME)
    v_min = cv2.getTrackbarPos("VALUE Min", WINDOW_NAME)
    v_max = cv2.getTrackbarPos("VALUE Max", WINDOW_NAME)
    return np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max])


def main() -> None:
    create_trackbars()
    cap = cv2.VideoCapture(VIDEO_PATH)
    frame_counter = 0

    while True:
        frame_counter += 1
        if cap.get(cv2.CAP_PROP_FRAME_COUNT) == frame_counter:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_counter = 0

        success, img = cap.read()
        if not success:
            break

        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower, upper = read_trackbar_bounds()
        mask = cv2.inRange(img_hsv, lower, upper)
        result = cv2.bitwise_and(img, img, mask=mask)
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        h_stack = np.hstack([img, mask_bgr, result])
        cv2.imshow("Horizontal Stacking", h_stack)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
