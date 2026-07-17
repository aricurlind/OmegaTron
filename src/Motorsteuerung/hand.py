"""Manuelle Tastatursteuerung von Omega-Tron über Pygame."""

import time
from typing import Final

import pygame
import RPi.GPIO as GPIO

import Motortreiber as m

GPIO.setmode(GPIO.BCM)

_STOP_TIMEOUT_S: Final = 0.5
_KEY_ACTIONS: Final = {
    'w': m.moveForward,
    's': m.moveBackward,
    'a': m.sharpLeft,
    'd': m.sharpRight,
    'q': m.swiftForwardLeft,
    'e': m.swiftForwardRight,
}


def init() -> None:
    pygame.init()
    pygame.display.set_mode((100, 100))


def getKey(key_name: str) -> bool:
    pygame.event.pump()
    key_input = pygame.key.get_pressed()
    key_code = getattr(pygame, f'K_{key_name}')
    pressed = bool(key_input[key_code])
    pygame.display.update()
    return pressed


def main(last_command_time: float) -> float:
    for key, action in _KEY_ACTIONS.items():
        if getKey(key):
            action()
            last_command_time = time.time()

    if (time.time() - last_command_time) > _STOP_TIMEOUT_S:
        m.stop()

    if getKey('x'):
        raise SystemExit

    return last_command_time


if __name__ == '__main__':
    init()
    last_command_time = 0.0
    while True:
        last_command_time = main(last_command_time)
