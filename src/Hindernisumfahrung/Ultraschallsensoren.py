"""Auslesen der fünf USS-Sensoren über die serielle Verbindung zum Arduino Nano.

Kapselt die Decodierung des Offset-Schemas aus USS_5.ino in eine
wiederverwendbare Klasse, damit sowohl die Hindernisumfahrung
(USS_Master.py) als auch die Müllerkennung (Detection_Modul.py) auf
dieselben Distanzwerte zugreifen können, statt den Sensor zweimal zu
initialisieren.

Erweiterungen gegenüber der ersten Fassung:
  - Jeder Sensor bekommt einen eigenen Medianfilter, da einzelne
    Fehlmessungen (Timeout, Mehrfachreflexion) sonst direkt in
    Ausweich-/Greifentscheidungen einfließen.
  - decode_raw_value() ist eine reine Funktion (kein self, kein I/O) und
    damit ohne echte serielle Verbindung testbar.
  - poll() versucht bei einem SerialException einen Reconnect statt
    abzustürzen, mit begrenzter Anzahl an Versuchen.
"""

import logging
import time
from typing import Dict, Optional

import serial

from filters import MedianFilter  # noqa: E402  (Pfad wird vom aufrufenden Skript ergänzt)

logger = logging.getLogger(__name__)

OFFSET_STEP = 500
SENSOR_NAMES = ("vorne", "vorne_rechts", "vorne_links", "rechts", "links")


def decode_raw_value(raw_value: float) -> Optional[Dict[str, float]]:
    """Decodiert einen rohen seriellen Messwert in {Sensorname: Distanz_cm}.

    Reine Funktion, damit das Offset-Schema unabhängig von einer echten
    seriellen Verbindung getestet werden kann.

    :return: Dictionary mit genau einem Eintrag, oder None bei ungültigem Wert.
    """
    sensor_index = int(raw_value // OFFSET_STEP)
    if not 0 <= sensor_index < len(SENSOR_NAMES):
        return None
    distance = raw_value - sensor_index * OFFSET_STEP
    return {SENSOR_NAMES[sensor_index]: distance}


class UltrasonicArray:
    """Liest, filtert und decodiert die Distanzwerte der fünf USS-Sensoren."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600, timeout: float = 1.0,
                 median_window: int = 5, reconnect_delay_s: float = 2.0,
                 max_reconnect_attempts: int = 5) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._reconnect_delay_s = reconnect_delay_s
        self._max_reconnect_attempts = max_reconnect_attempts

        self._serial = serial.Serial(port, baudrate, timeout=timeout)
        self._serial.flush()

        self._filters: Dict[str, MedianFilter] = {
            name: MedianFilter(window_size=median_window) for name in SENSOR_NAMES
        }
        self._last_distances: Dict[str, float] = {name: float(OFFSET_STEP) for name in SENSOR_NAMES}

    def _reconnect(self) -> bool:
        for attempt in range(1, self._max_reconnect_attempts + 1):
            logger.warning("USS-Verbindung verloren, Reconnect-Versuch %s/%s ...",
                            attempt, self._max_reconnect_attempts)
            try:
                self._serial.close()
            except serial.SerialException:
                pass
            time.sleep(self._reconnect_delay_s)
            try:
                self._serial = serial.Serial(self._port, self._baudrate, timeout=self._timeout)
                self._serial.flush()
                logger.info("USS-Verbindung wiederhergestellt.")
                return True
            except serial.SerialException:
                continue
        logger.error("USS-Reconnect nach %s Versuchen fehlgeschlagen. Fahre mit letzten bekannten Werten fort.",
                      self._max_reconnect_attempts)
        return False

    def poll(self) -> Dict[str, float]:
        """Liest alle aktuell im Puffer verfügbaren Messwerte, filtert sie und aktualisiert den Zustand.

        Bei einem Verbindungsabbruch wird versucht, neu zu verbinden; bis
        das gelingt (oder die Versuche aufgebraucht sind) werden die
        zuletzt bekannten, gefilterten Distanzen zurückgegeben, statt das
        Programm abstürzen zu lassen.

        :return: Die zuletzt bekannten, gefilterten Distanzen (in cm) aller fünf Sensoren.
        """
        try:
            while self._serial.in_waiting > 0:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                try:
                    raw_value = float(line)
                except ValueError:
                    logger.warning("Konnte USS-Zeile nicht parsen: %r", line)
                    continue

                decoded = decode_raw_value(raw_value)
                if decoded is None:
                    logger.warning("Unerwarteter Rohwert von den USS-Sensoren: %s", raw_value)
                    continue

                for name, distance in decoded.items():
                    filtered = self._filters[name].update(distance)
                    self._last_distances[name] = filtered
        except serial.SerialException:
            self._reconnect()

        return dict(self._last_distances)

    def closest_sensor(self) -> str:
        """Name des Sensors mit der aktuell geringsten gefilterten Distanz."""
        distances = self.poll()
        return min(distances, key=distances.get)

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()

    def __enter__(self) -> "UltrasonicArray":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
