"""Fahrbefehle für Omega-Tron: benannte Manöver und kontinuierliches Mixing."""

import time
from typing import Final, Tuple

import RPi.GPIO as GPIO

from AMSpi import AMSpi

GPIO.setmode(GPIO.BCM)

_SHIFT_REGISTER_PINS: Final = (21, 20, 16)
_L293D_PWM_PINS: Final = (5, 6, 13, 19)
_COMMAND_HOLD_S: Final = 0.1


def _with_amspi() -> AMSpi:
    amspi = AMSpi()
    amspi.set_74HC595_pins(*_SHIFT_REGISTER_PINS)
    amspi.set_L293D_pins(*_L293D_PWM_PINS)
    return amspi


def moveBackward() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motors([amspi.DC_Motor_1, amspi.DC_Motor_2, amspi.DC_Motor_3, amspi.DC_Motor_4], True, 100)
        time.sleep(_COMMAND_HOLD_S)


def moveForward() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motors([amspi.DC_Motor_1, amspi.DC_Motor_2, amspi.DC_Motor_3, amspi.DC_Motor_4], False, 100)
        time.sleep(_COMMAND_HOLD_S)


def sharpRight() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_1, True, 100)
        amspi.run_dc_motor(amspi.DC_Motor_3, False, 100)
        amspi.run_dc_motor(amspi.DC_Motor_2, True, 100)
        amspi.run_dc_motor(amspi.DC_Motor_4, False, 100)
        time.sleep(_COMMAND_HOLD_S)


def sharpLeft() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_2, False, 100)
        amspi.run_dc_motor(amspi.DC_Motor_4, True, 100)
        amspi.run_dc_motor(amspi.DC_Motor_1, False, 100)
        amspi.run_dc_motor(amspi.DC_Motor_3, True, 100)
        time.sleep(_COMMAND_HOLD_S)


def swiftForwardRight() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_4, False, 10)
        amspi.run_dc_motor(amspi.DC_Motor_2, True, 100)
        amspi.run_dc_motor(amspi.DC_Motor_3, True, 0)
        amspi.run_dc_motor(amspi.DC_Motor_1, True, 100)
        time.sleep(_COMMAND_HOLD_S)


def swiftForwardLeft() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_4, True, 100)
        amspi.run_dc_motor(amspi.DC_Motor_2, False, 10)
        amspi.run_dc_motor(amspi.DC_Motor_1, True, 0)
        amspi.run_dc_motor(amspi.DC_Motor_3, True, 100)
        time.sleep(_COMMAND_HOLD_S)


def swiftBackwardRight() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_1, False, 80)
        amspi.run_dc_motor(amspi.DC_Motor_3, False, 100)
        amspi.run_dc_motor(amspi.DC_Motor_2, False, 50)
        amspi.run_dc_motor(amspi.DC_Motor_4, False, 30)
        time.sleep(_COMMAND_HOLD_S)


def swiftBackwardLeft() -> None:
    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_4, False, 80)
        amspi.run_dc_motor(amspi.DC_Motor_2, False, 100)
        amspi.run_dc_motor(amspi.DC_Motor_1, False, 50)
        amspi.run_dc_motor(amspi.DC_Motor_3, False, 30)
        time.sleep(_COMMAND_HOLD_S)


def stop() -> None:
    with _with_amspi() as amspi:
        amspi.stop_dc_motors([amspi.DC_Motor_1, amspi.DC_Motor_2, amspi.DC_Motor_3, amspi.DC_Motor_4])
        time.sleep(_COMMAND_HOLD_S)


def mix_differential_drive(speed: float, steering: float) -> Tuple[float, float]:
    """Berechnet die normierten Radgeschwindigkeiten aus Speed/Steering.

    Reine Funktion ohne Hardwarezugriff, damit die Mischlogik unabhängig
    von GPIO/AMSpi getestet werden kann.

    :param speed: Vorwärts-/Rückwärtsgeschwindigkeit im Bereich [-1.0, 1.0].
    :param steering: Lenkwert im Bereich [-1.0, 1.0]; negativ = links, positiv = rechts.
    :return: (left_speed, right_speed), je im Bereich [-1.0, 1.0].
    """
    speed = max(-1.0, min(1.0, speed))
    steering = max(-1.0, min(1.0, steering))

    left_speed = speed - steering
    right_speed = speed + steering
    # left_speed, right_speed = speed + steering, speed - steering  # Vorzeichen vertauscht, Auto lenkte spiegelverkehrt
    max_magnitude = max(abs(left_speed), abs(right_speed), 1.0)
    return left_speed / max_magnitude, right_speed / max_magnitude


def move(speed: float, steering: float, t: float = _COMMAND_HOLD_S) -> None:
    """Differentialantrieb aus kontinuierlichen Werten mischen.

    Wird von der Datensammlung (PS4-Steuerung), der CNN-Fahrt und der
    PID-geregelten Fahrspurfolge in main.py verwendet, die alle ein
    stufenloses Geschwindigkeits-/Lenksignal statt fester Manöver benötigen.
    Diese Funktion fehlte im Originalprojekt, obwohl sie von LogMain.py und
    Omega_Tron_CNN_Main.py bereits aufgerufen wurde.

    Annahme zur Radzuordnung (aus den sharpLeft/sharpRight-Manövern
    abgeleitet): DC_Motor_1/DC_Motor_3 = linke Seite, DC_Motor_2/DC_Motor_4
    = rechte Seite. Bei abweichender Verkabelung ggf. anpassen.

    :param speed: Vorwärts-/Rückwärtsgeschwindigkeit im Bereich [-1.0, 1.0].
    :param steering: Lenkwert im Bereich [-1.0, 1.0]; negativ = links, positiv = rechts.
    :param t: Dauer, für die der Befehl gehalten wird, in Sekunden.
    """
    left_speed, right_speed = mix_differential_drive(speed, steering)

    left_duty = int(abs(left_speed) * 100)
    right_duty = int(abs(right_speed) * 100)
    left_clockwise = left_speed >= 0
    right_clockwise = right_speed >= 0

    with _with_amspi() as amspi:
        amspi.run_dc_motor(amspi.DC_Motor_1, left_clockwise, left_duty)
        amspi.run_dc_motor(amspi.DC_Motor_3, left_clockwise, left_duty)
        amspi.run_dc_motor(amspi.DC_Motor_2, right_clockwise, right_duty)
        amspi.run_dc_motor(amspi.DC_Motor_4, right_clockwise, right_duty)
        time.sleep(t)
