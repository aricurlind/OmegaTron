"""PCA9685 PWM/Servo-Controller-Treiber (I2C)."""

from __future__ import division

import logging
import math
import time
from typing import Optional

PCA9685_ADDRESS = 0x40

MODE1 = 0x00
MODE2 = 0x01
SUBADR1 = 0x02
SUBADR2 = 0x03
SUBADR3 = 0x04
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

RESTART = 0x80
SLEEP = 0x10
ALLCALL = 0x01
INVRT = 0x10
OUTDRV = 0x04

logger = logging.getLogger(__name__)


def software_reset(i2c=None, **kwargs) -> None:
    """Sendet einen Software-Reset an alle Servo-Controller auf dem I2C-Bus."""
    if i2c is None:
        import Adafruit_GPIO.I2C as I2C
        i2c = I2C
    device = i2c.get_i2c_device(0x00, **kwargs)
    device.writeRaw8(0x06)  # SWRST


class PCA9685:
    """PCA9685 PWM LED/Servo-Controller."""

    def __init__(self, address: int = PCA9685_ADDRESS, i2c=None, **kwargs) -> None:
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)
        self.set_all_pwm(0, 0)
        self._device.write8(MODE2, OUTDRV)
        self._device.write8(MODE1, ALLCALL)
        time.sleep(0.005)
        mode1 = self._device.readU8(MODE1)
        mode1 = mode1 & ~SLEEP
        self._device.write8(MODE1, mode1)
        time.sleep(0.005)

    def set_pwm_freq(self, freq_hz: float) -> None:
        """Setzt die PWM-Frequenz aller Kanäle in Hz."""
        prescaleval = 25000000.0 / 4096.0 / float(freq_hz) - 1.0
        prescale = int(math.floor(prescaleval + 0.5))
        oldmode = self._device.readU8(MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        self._device.write8(MODE1, newmode)
        self._device.write8(PRESCALE, prescale)
        self._device.write8(MODE1, oldmode)
        time.sleep(0.005)
        self._device.write8(MODE1, oldmode | 0x80)

    def set_pwm(self, channel: int, on: int, off: int) -> None:
        """Setzt Ein-/Ausschaltzeitpunkt eines einzelnen PWM-Kanals."""
        self._device.write8(LED0_ON_L + 4 * channel, on & 0xFF)
        self._device.write8(LED0_ON_H + 4 * channel, on >> 8)
        self._device.write8(LED0_OFF_L + 4 * channel, off & 0xFF)
        self._device.write8(LED0_OFF_H + 4 * channel, off >> 8)

    def set_all_pwm(self, on: int, off: int) -> None:
        """Setzt Ein-/Ausschaltzeitpunkt aller PWM-Kanäle gleichzeitig."""
        self._device.write8(ALL_LED_ON_L, on & 0xFF)
        self._device.write8(ALL_LED_ON_H, on >> 8)
        self._device.write8(ALL_LED_OFF_L, off & 0xFF)
        self._device.write8(ALL_LED_OFF_H, off >> 8)
