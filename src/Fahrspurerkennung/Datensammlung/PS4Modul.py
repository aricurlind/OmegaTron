"""PS4-Controller-Anbindung über Pygame.

Diese Datei wurde von LogMain.py importiert, war im Originalprojekt aber
nicht enthalten. Sie stellt die dort erwartete Schnittstelle getJS() bereit,
die die Achsen- und Tastenwerte des Controllers als Dictionary liefert.
"""

from typing import Dict, Union

import pygame

_AXIS_STEERING: int = 0
_AXIS_THROTTLE: int = 1
_BUTTON_SHARE: int = 8
_DEADZONE: float = 0.05

_joystick: pygame.joystick.Joystick = None


def init() -> None:
    """Initialisiert Pygame und verbindet den ersten erkannten Controller."""
    global _joystick
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        raise RuntimeError("Kein PS4-Controller gefunden.")
    _joystick = pygame.joystick.Joystick(0)
    _joystick.init()


def _apply_deadzone(value: float) -> float:
    return 0.0 if abs(value) < _DEADZONE else value


def getJS() -> Dict[str, Union[float, int]]:
    """Liest den aktuellen Zustand des Controllers aus.

    :return: Dictionary mit 'axis1' (Lenkung), 'x' (Geschwindigkeit) und
        'share' (1 während gedrückt gehalten, sonst 0).
    """
    if _joystick is None:
        init()

    pygame.event.pump()
    axis1 = _apply_deadzone(_joystick.get_axis(_AXIS_STEERING))
    axis_x = _apply_deadzone(_joystick.get_axis(_AXIS_THROTTLE))
    share = 1 if _joystick.get_button(_BUTTON_SHARE) else 0

    return {'axis1': axis1, 'x': axis_x, 'share': share}


if __name__ == '__main__':
    init()
    while True:
        print(getJS())
        pygame.time.wait(100)
