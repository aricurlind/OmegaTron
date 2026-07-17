"""Steuerung des 4-DOF-Roboterarms für Greifen und Entsorgen von Müll.

Kanal-Zuordnung:
    Hüfte    -> Kanal 2
    Schulter -> Kanal 7
    Ellbogen -> Kanal 6
    Greifer  -> Kanal 3

Referenzwerte Greifer:
    160 = zu, 300 = 90° (halb offen), 450 = 180° (weit offen), 600 = ganz auf

Referenzwerte Schulter:
    75 = ganz oben, 300 = 90°, 450 = 45°, 620 = ganz unten

Referenzwerte Ellbogen:
    300 = 90°, 400 = 70°, 500 = 45°, 550 = 20°, 600 = 0°
"""

import time, json
from typing import Final, List, Tuple

import Adafruit_PCA9685

CHANNEL_HUEFTE: Final = 2
CHANNEL_SCHULTER: Final = 7
CHANNEL_ELLBOGEN: Final = 6
CHANNEL_GREIFER: Final = 3

PWM_FREQUENCY_HZ: Final = 60
STEP_DELAY_S: Final = 1.0

# Jede Sequenz ist eine Liste aus (Kanal, PWM-Wert)-Schritten, die
# nacheinander mit STEP_DELAY_S Pause angefahren werden.

_pwm: Adafruit_PCA9685.PCA9685 = None


def _get_controller() -> Adafruit_PCA9685.PCA9685:
    global _pwm
    if _pwm is None:
        _pwm = Adafruit_PCA9685.PCA9685()
        _pwm.set_pwm_freq(PWM_FREQUENCY_HZ)
        print("Roboterarm bereit. Zum Beenden Ctrl-C drücken...")
    return _pwm


def _run_sequence(steps: List[Tuple[int, int]]) -> None:
    pwm = _get_controller()
    for channel, value in steps:
        pwm.set_pwm(channel, 0, value)
        time.sleep(STEP_DELAY_S)


def _load_sequences(path: str = "robot_sequences.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # JSON → Kanäle ersetzen
    name_to_channel = {
        "Huefte": CHANNEL_HUEFTE,
        "Schulter": CHANNEL_SCHULTER,
        "Ellbogen": CHANNEL_ELLBOGEN,
        "Greifer": CHANNEL_GREIFER,
    }

    sequences = {}
    for mode, steps in raw.items():
        sequences[mode] = [
            (name_to_channel[name], int(pwm)) for name, pwm in steps
        ]

    return sequences


def Roboterarm(mode: str) -> None:
    sequences = _load_sequences()

    if mode not in sequences:
        raise ValueError(f"Unbekannter Modus: {mode!r}. Erlaubt: {list(sequences)}")

    _run_sequence(sequences[mode])
