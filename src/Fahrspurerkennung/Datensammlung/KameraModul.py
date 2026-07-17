"""Kamera-Wrapper für die Fahrspurerkennung und Datensammlung."""

from typing import Tuple

import cv2

_cap = cv2.VideoCapture(0)


def getImg(display: bool = False, size: Tuple[int, int] = (480, 240)):
    """Liest ein Kamerabild und skaliert es auf die gewünschte Größe.

    :param display: Wenn True, wird das Bild zusätzlich in einem Fenster angezeigt.
    :param size: Zielgröße (Breite, Höhe) in Pixeln.
    """
    success, img = _cap.read()
    if not success:
        raise RuntimeError("Konnte kein Kamerabild lesen.")
    img = cv2.resize(img, (size[0], size[1]))
    if display:
        cv2.imshow("Fahrspur", img)
        cv2.waitKey(1)
    return img


if __name__ == "__main__":
    while True:
        getImg(True)
