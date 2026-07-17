"""Filter zur Rauschunterdrückung für Sensordaten.

Die Ultraschallsensoren liefern gelegentlich Ausreißer (z. B. bei
Mehrfachreflexion oder Timeout im pulseIn). Ungefiltert konnte das bisher
direkt zu einem falschen Ausweich- oder Greifmanöver führen.
"""

from collections import deque
from typing import Deque


class MedianFilter:
    """Gleitender Medianfilter, robust gegen einzelne Ausreißer.

    Im Gegensatz zu einem gleitenden Mittelwert wird ein einzelner
    Fehlmesswert (z. B. 500 cm durch ein Timeout) nicht anteilig in die
    Ausgabe gemischt, solange er nicht die Mehrheit des Fensters stellt.
    """

    def __init__(self, window_size: int = 5) -> None:
        if window_size < 1:
            raise ValueError("window_size muss >= 1 sein.")
        self._buffer: Deque[float] = deque(maxlen=window_size)

    def update(self, value: float) -> float:
        self._buffer.append(value)
        ordered = sorted(self._buffer)
        return ordered[len(ordered) // 2]

    def reset(self) -> None:
        self._buffer.clear()


class KalmanFilter1D:
    """Vereinfachter Kalman-Filter für ein 1D-Konstantwert-Modell.

    Es wird bewusst kein Bewegungsmodell (Geschwindigkeit/Beschleunigung)
    angenommen, da sich die Distanz zwischen zwei Messzyklen (~50-100 ms bei
    5 Sensoren) im Vergleich zur Fahrzeuggeschwindigkeit nur wenig ändert.
    process_variance und measurement_variance sind grobe Startwerte und
    sollten mit realen Sensordaten (Stillstand vs. Fahrt) kalibriert werden.
    """

    def __init__(self, process_variance: float = 1e-2, measurement_variance: float = 4.0,
                 initial_estimate: float = 0.0, initial_error: float = 1.0) -> None:
        self._process_variance = process_variance
        self._measurement_variance = measurement_variance
        self._estimate = initial_estimate
        self._error = initial_error

    def update(self, measurement: float) -> float:
        predicted_error = self._error + self._process_variance

        kalman_gain = predicted_error / (predicted_error + self._measurement_variance)
        self._estimate = self._estimate + kalman_gain * (measurement - self._estimate)
        self._error = (1 - kalman_gain) * predicted_error
        return self._estimate

    def reset(self, initial_estimate: float = 0.0, initial_error: float = 1.0) -> None:
        self._estimate = initial_estimate
        self._error = initial_error
