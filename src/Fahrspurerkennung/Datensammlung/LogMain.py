"""Sammelt Trainingsdaten (Bild + Lenkwinkel) über die PS4-Fernsteuerung."""

from time import sleep
from typing import Final

import cv2

import KameraModul as kM
import LogModul as LM
import Motortreiber as m
import PS4Modul as PM

MAX_SPEED: Final = 0.8
RECORD_TOGGLE_DEBOUNCE_S: Final = 0.1


def main() -> None:
    record = 0
    while True:
        joystick = PM.getJS()
        steering = joystick["axis1"]
        speed = joystick["x"] * -MAX_SPEED

        if joystick["share"] == 1:
            record = 1 if record == 0 else 2
            if record == 1:
                print("Aufzeichnung begonnen ...")
            sleep(RECORD_TOGGLE_DEBOUNCE_S)

        if record == 1:
            img = kM.getImg(True, size=(240, 120))
            LM.saveData(img, -steering)
        elif record == 2:
            LM.saveLog()
            record = 0

        m.move(speed, -steering, t=0.1)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()
