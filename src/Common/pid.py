"""Generischer PID-Regler mit Anti-Windup und Ausgangsbegrenzung.

Wird sowohl für die Fahrspurlenkung (main.py) als auch für die
Objektzentrierung (Objekterkennung/Detection_Modul.py) verwendet. Bisher
wurde in beiden Fällen mit einer festen Geschwindigkeit in Richtung des
Fehlers gefahren ("Bang-Bang"), unabhängig davon, wie groß die Abweichung
tatsächlich war. Das führte bei kleinen Abweichungen zu unnötigem
Überschwingen und bei großen zu langsamer Reaktion.
"""

import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class PIDGains:
    kp: float
    ki: float = 0.0
    kd: float = 0.0


class PIDController:
    """Zeitdiskreter PID-Regler mit Clamping-Anti-Windup.

    Der Regler ist zustandsbehaftet (Integralanteil, letzter Fehler,
    Zeitstempel) und muss daher pro Regelstrecke eine eigene Instanz
    bekommen, nicht global geteilt werden.
    """

    def __init__(self, gains: PIDGains, output_limits: Tuple[float, float] = (-1.0, 1.0),
                 integral_limits: Optional[Tuple[float, float]] = None) -> None:
        self._gains = gains
        self._out_min, self._out_max = output_limits
        self._integral_min, self._integral_max = integral_limits or output_limits
        self._integral = 0.0
        self._prev_error: Optional[float] = None
        self._prev_time: Optional[float] = None

    def reset(self) -> None:
        """Setzt Integral- und Differentialzustand zurück (z. B. bei Modus-/Zielwechsel)."""
        self._integral = 0.0
        self._prev_error = None
        self._prev_time = None

    def update(self, error: float, now: Optional[float] = None) -> float:
        """Berechnet die Stellgröße für den aktuellen Regelfehler.

        :param error: Regelfehler (Sollwert - Istwert bzw. hier direkt der
            gemessene Versatz, da der Sollwert per Definition 0 ist).
        :param now: Zeitstempel in Sekunden (monotonic), hauptsächlich für
            Tests. Standardmäßig time.monotonic().
        """
        now = now if now is not None else time.monotonic()
        dt = (now - self._prev_time) if self._prev_time is not None else 0.0
        self._prev_time = now

        p_term = self._gains.kp * error

        # Anti-Windup per Clamping: Integral nur akkumulieren, wenn dt gültig
        # ist, und danach sofort begrenzen, statt erst am Ausgang zu clippen.
        if dt > 0:
            self._integral += error * dt
            self._integral = max(self._integral_min, min(self._integral_max, self._integral))
        i_term = self._gains.ki * self._integral

        d_term = 0.0
        if dt > 0 and self._prev_error is not None:
            d_term = self._gains.kd * (error - self._prev_error) / dt
        # d_term = self._gains.kd * (error - self._prev_error)  # dt-Division vergessen, driftete bei wechselnder Zykluszeit
        self._prev_error = error

        output = p_term + i_term + d_term
        return max(self._out_min, min(self._out_max, output))
