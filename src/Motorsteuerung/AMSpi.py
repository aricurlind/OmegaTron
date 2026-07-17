#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMSpi class - Python class for controlling Arduino Motor Shield L293D from Raspberry Pi.

.. Licence MIT
.. codeauthor:: Jan Lipovsky <janlipovsky@gmail.com>, janlipovsky.cz
.. contributors: Daniel Neumann
"""

import logging
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import RPi.GPIO as GPIO
except RuntimeError as exc:
    raise RuntimeError(
        "Failed to import RPi.GPIO. This usually means the script was not "
        "started with sufficient privileges. Run it with 'sudo'."
    ) from exc

logger = logging.getLogger(__name__)


class AMSpi:
    """Controls an Arduino Motor Shield L293D via Raspberry Pi GPIO (RPi.GPIO)."""

    DC_Motor_1 = 1
    DC_Motor_2 = 2
    DC_Motor_3 = 3
    DC_Motor_4 = 4

    _PIN_ = 1
    _DIRECTION_ = 2
    _IS_RUNNING_ = 3
    _RUNNING_DIRECTION_ = 4
    _PWM_ = 5
    _PWM_FREQUENCY_ = 6
    _PWM_DUTY_CYCLE_ = 7

    _CLOCKWISE = 0
    _COUNTERCLOCKWISE = 1
    _STOP = 2

    def __init__(self, use_board: bool = False) -> None:
        self._motors: Dict[int, Dict[int, object]] = {
            self.DC_Motor_1: {self._PIN_: None, self._DIRECTION_: [4, 8, 4 | 8], self._IS_RUNNING_: False,
                               self._RUNNING_DIRECTION_: None, self._PWM_FREQUENCY_: 10,
                               self._PWM_DUTY_CYCLE_: 100, self._PWM_: None},
            self.DC_Motor_2: {self._PIN_: None, self._DIRECTION_: [2, 16, 2 | 16], self._IS_RUNNING_: False,
                               self._RUNNING_DIRECTION_: None, self._PWM_FREQUENCY_: 10,
                               self._PWM_DUTY_CYCLE_: 100, self._PWM_: None},
            self.DC_Motor_3: {self._PIN_: None, self._DIRECTION_: [32, 128, 32 | 128], self._IS_RUNNING_: False,
                               self._RUNNING_DIRECTION_: None, self._PWM_FREQUENCY_: 10,
                               self._PWM_DUTY_CYCLE_: 100, self._PWM_: None},
            self.DC_Motor_4: {self._PIN_: None, self._DIRECTION_: [1, 64, 1 | 64], self._IS_RUNNING_: False,
                               self._RUNNING_DIRECTION_: None, self._PWM_FREQUENCY_: 10,
                               self._PWM_DUTY_CYCLE_: 100, self._PWM_: None},
        }
        self._dir_latch: Optional[int] = None
        self._dir_clk: Optional[int] = None
        self._dir_ser: Optional[int] = None

        if use_board:
            GPIO.setmode(GPIO.BOARD)
            logger.info("PIN numbering: BOARD")
        else:
            GPIO.setmode(GPIO.BCM)
            logger.info("PIN numbering: BCM")

    def __enter__(self) -> "AMSpi":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        try:
            if self._shift_pins_configured():
                self._shift_write(0)
            GPIO.cleanup()
        except RuntimeWarning:
            return True
        return False

    def _shift_pins_configured(self) -> bool:
        return None not in (self._dir_latch, self._dir_clk, self._dir_ser)

    def _shift_write(self, value: int) -> None:
        if not self._shift_pins_configured():
            logger.error("PINs for shift register were not set properly.")
            self.__exit__(None, None, None)
            return

        GPIO.output(self._dir_latch, GPIO.LOW)
        for _ in range(8):
            bit = value & 0x80
            GPIO.output(self._dir_clk, GPIO.LOW)
            GPIO.output(self._dir_ser, GPIO.HIGH if bit == 0x80 else GPIO.LOW)
            GPIO.output(self._dir_clk, GPIO.HIGH)
            value <<= 0x01
        GPIO.output(self._dir_latch, GPIO.HIGH)

    def set_74HC595_pins(self, dir_latch: int, dir_clk: int, dir_ser: int) -> None:
        self._dir_latch = dir_latch
        self._dir_clk = dir_clk
        self._dir_ser = dir_ser
        GPIO.setup(self._dir_latch, GPIO.OUT)
        GPIO.setup(self._dir_clk, GPIO.OUT)
        GPIO.setup(self._dir_ser, GPIO.OUT)

    def set_L293D_pins(self, PWM0A: Optional[int] = None, PWM0B: Optional[int] = None,
                        PWM2A: Optional[int] = None, PWM2B: Optional[int] = None) -> None:
        self._motors[self.DC_Motor_4][self._PIN_] = PWM0B
        self._motors[self.DC_Motor_3][self._PIN_] = PWM0A
        self._motors[self.DC_Motor_1][self._PIN_] = PWM2A
        self._motors[self.DC_Motor_2][self._PIN_] = PWM2B
        for pin in (PWM0A, PWM0B, PWM2A, PWM2B):
            if pin is not None:
                GPIO.setup(pin, GPIO.OUT)

    def _get_motors_direction(self, dc_motor: int, directions_index: int) -> Tuple[int, int]:
        direction_value = self._motors[dc_motor][self._DIRECTION_][directions_index]
        all_motors_direction = direction_value
        for other_motor in (self.DC_Motor_1, self.DC_Motor_2, self.DC_Motor_3, self.DC_Motor_4):
            if other_motor == dc_motor:
                continue
            running_direction = self._motors[other_motor][self._RUNNING_DIRECTION_]
            if running_direction is not None:
                all_motors_direction += running_direction
        return all_motors_direction, direction_value

    def set_pwm_frequency(self, motors_freq: Dict[int, int]) -> None:
        assert all(motor in self._motors for motor in motors_freq), "Unknown motor was set."
        for motor, freq in motors_freq.items():
            self._motors[motor][self._PWM_FREQUENCY_] = freq

    def get_pwm_frequency(self) -> Dict[int, int]:
        return {motor: self._motors[motor][self._PWM_FREQUENCY_] for motor in self._motors}

    def get_pwm_duty_cycle(self) -> Dict[int, int]:
        return {motor: self._motors[motor][self._PWM_DUTY_CYCLE_] for motor in self._motors}

    def run_dc_motor(self, dc_motor: int, clockwise: bool = True, speed: Optional[float] = None) -> bool:
        if self._motors[dc_motor][self._PIN_] is None:
            logger.warning("Pin for DC_Motor_%s is not set. Cannot run motor.", dc_motor)
            return False

        all_motors_direction, direction_value = self._get_motors_direction(dc_motor, int(not clockwise))
        self._shift_write(all_motors_direction)

        if speed is None:
            if self._motors[dc_motor][self._PWM_] is not None:
                self._motors[dc_motor][self._PWM_].stop()
                self._motors[dc_motor][self._PWM_] = None
            GPIO.output(self._motors[dc_motor][self._PIN_], GPIO.HIGH)
        elif 0 <= speed <= 100:
            self._motors[dc_motor][self._PWM_DUTY_CYCLE_] = speed
            if self._motors[dc_motor][self._PWM_] is None:
                pwm = GPIO.PWM(self._motors[dc_motor][self._PIN_], self._motors[dc_motor][self._PWM_FREQUENCY_])
                pwm.start(self._motors[dc_motor][self._PWM_DUTY_CYCLE_])
                self._motors[dc_motor][self._PWM_] = pwm
            else:
                self._motors[dc_motor][self._PWM_].ChangeDutyCycle(self._motors[dc_motor][self._PWM_DUTY_CYCLE_])
        else:
            logger.warning("Speed must be in range 0-100 (got %s). Keeping previous setting (%s).",
                            speed, self._motors[dc_motor][self._PWM_DUTY_CYCLE_])

        self._motors[dc_motor][self._IS_RUNNING_] = True
        self._motors[dc_motor][self._RUNNING_DIRECTION_] = direction_value
        return True

    def run_dc_motors(self, dc_motors: Iterable[int], clockwise: bool = True, speed: Optional[float] = None) -> None:
        for dc_motor in dc_motors:
            self.run_dc_motor(dc_motor, clockwise, speed)

    def stop_dc_motor(self, dc_motor: int) -> bool:
        if self._motors[dc_motor][self._PIN_] is None:
            return False

        all_motors_direction, _ = self._get_motors_direction(dc_motor, self._STOP)
        self._shift_write(all_motors_direction)

        if self._motors[dc_motor][self._PWM_] is None:
            GPIO.output(self._motors[dc_motor][self._PIN_], GPIO.LOW)
        else:
            self._motors[dc_motor][self._PWM_].stop()
            self._motors[dc_motor][self._PWM_] = None

        self._motors[dc_motor][self._IS_RUNNING_] = False
        self._motors[dc_motor][self._RUNNING_DIRECTION_] = None
        return True

    def stop_dc_motors(self, dc_motors: List[int]) -> bool:
        return all(self.stop_dc_motor(dc_motor) for dc_motor in dc_motors)
