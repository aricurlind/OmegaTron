"""Nebenläufigkeits-Hilfsmittel für die Regelschleife in main.py.

Ohne Entkopplung blockiert cv2.VideoCapture.read() die Regelschleife für eine
variable, treiberabhängige Zeit – das verfälscht die Zykluszeit, auf der die
PID-Regler in Common/pid.py basieren (dt fließt direkt in I- und D-Anteil
ein). ThreadedVideoStream hält das Kamerabild in einem Hintergrundthread
aktuell; FixedRateLoop sorgt dafür, dass der Regelkreis selbst mit fester
Frequenz statt "so schnell wie möglich" läuft.
"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class ThreadedVideoStream:
    """Liest kontinuierlich Kamerabilder in einem Hintergrundthread."""

    def __init__(self, camera_index: int = 0) -> None:
        import cv2  # lokal importiert, damit dieses Modul auch ohne OpenCV testbar bleibt
        self._cap = cv2.VideoCapture(camera_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Kamera {camera_index} konnte nicht geöffnet werden.")
        self._lock = threading.Lock()
        self._frame = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "ThreadedVideoStream":
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        return self

    def _update_loop(self) -> None:
        while self._running:
            success, frame = self._cap.read()
            if success:
                with self._lock:
                    self._frame = frame
            else:
                logger.warning("Kein Kamerabild erhalten, versuche erneut.")
                time.sleep(0.01)

    def read(self):
        """Gibt das zuletzt eingelesene Bild zurück (Kopie) oder None, falls noch keines vorliegt."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    @property
    def raw_capture(self):
        """Zugriff auf das zugrundeliegende cv2.VideoCapture, z. B. für WasteCollector."""
        return self._cap

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._cap.release()

    def __enter__(self) -> "ThreadedVideoStream":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


class FixedRateLoop:
    """Taktet eine Regelschleife auf eine feste Zielfrequenz.

    Läuft ein Zyklus länger als die Periode, wird die Verzögerung nicht
    nachträglich aufgeholt (das würde sonst zu einer Salve von Zyklen mit
    dt=0 führen) – der nächste Tick wird stattdessen direkt an die aktuelle
    Zeit angehängt.
    """

    def __init__(self, frequency_hz: float) -> None:
        if frequency_hz <= 0:
            raise ValueError("frequency_hz muss > 0 sein.")
        self._period = 1.0 / frequency_hz
        self._last_tick = time.monotonic()

    def wait(self) -> float:
        """Blockiert bis zum nächsten Zyklusbeginn und gibt die tatsächliche dt zurück."""
        now = time.monotonic()
        elapsed = now - self._last_tick
        remaining = self._period - elapsed
        if remaining > 0:
            time.sleep(remaining)
            dt = self._period
        else:
            logger.debug("Regelschleife überzogen um %.3f s.", -remaining)
            dt = elapsed
        self._last_tick = time.monotonic()
        return dt
