"""Omega-Tron Hauptprogramm.

Verbindet die drei bislang unabhängigen Teilsysteme zu einem durchgehenden
Ablauf. Priorität pro Zyklus:

  1. HINDERNISUMFAHRUNG – falls ein Sensor unterhalb von SAFETY_DISTANCE_CM
     meldet, hat Ausweichen Vorrang vor allem anderen.
  2. MUELLSAMMLUNG       – wird im aktuellen Kamerabild mit ausreichender
     Konfidenz Müll erkannt, übernimmt der WasteCollector die Kontrolle,
     bis das Objekt eingesammelt ist, und gibt sie danach zurück.
  3. FAHRSPURFOLGE        – ansonsten hält Omega-Tron die Fahrspur mittig,
     PID-geregelt auf Basis des Kurvenversatzes aus getLaneCurve().

Kamera und Ultraschallsensorik werden hier genau einmal geöffnet und an die
Teilsysteme weitergereicht, damit sie sich nicht gegenseitig blockieren.
Die Kamera läuft in einem Hintergrundthread (ThreadedVideoStream), damit
variable Latenzen von cv2.VideoCapture.read() nicht die Zykluszeit der
Regelschleife verfälschen, auf der die PID-Regler basieren.
"""

import logging
import os
import sys

import cv2

_ROOT = os.path.dirname(os.path.abspath(__file__))
for _subfolder in ("Common", "Motorsteuerung", "Hindernisumfahrung", "Objekterkennung",
                    "Roboterarm", "Fahrspurerkennung/AlgorithmusOhneDL"):
    sys.path.append(os.path.join(_ROOT, _subfolder))

import Motortreiber as motor  # noqa: E402
from Ultraschallsensoren import UltrasonicArray  # noqa: E402
from USS_Master import choose_maneuver  # noqa: E402
from Detection_Modul import WasteCollector  # noqa: E402
from LaneDetection import getLaneCurve  # noqa: E402
import Hilfsfunktionen  # noqa: E402
from pid import PIDController, PIDGains  # noqa: E402
from video_stream import ThreadedVideoStream, FixedRateLoop  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CAMERA_INDEX: int = 0
USS_PORT: str = "/dev/ttyUSB0"

SAFETY_DISTANCE_CM: float = 25.0
LANE_FOLLOW_SPEED: float = 0.5
LANE_STEERING_GAINS = PIDGains(kp=0.8, ki=0.05, kd=0.15)
DETECTION_CONFIDENCE_MIN: float = 0.6
LANE_TRACKBAR_INITIAL = [102, 80, 20, 214]
CONTROL_LOOP_HZ: float = 10.0


def main() -> None:
    steering_pid = PIDController(LANE_STEERING_GAINS, output_limits=(-1.0, 1.0))
    loop = FixedRateLoop(CONTROL_LOOP_HZ)

    Hilfsfunktionen.initializeTrackbars(LANE_TRACKBAR_INITIAL)

    with ThreadedVideoStream(CAMERA_INDEX) as stream, \
            UltrasonicArray(port=USS_PORT) as sensors, \
            WasteCollector(capture=stream.raw_capture, sensors=sensors) as collector:
        try:
            while True:
                dt = loop.wait()

                distances = sensors.poll()
                if min(distances.values()) < SAFETY_DISTANCE_CM:
                    logger.info("Hindernis erkannt: %s", distances)
                    choose_maneuver(distances)
                    steering_pid.reset()  # Regler soll nach dem Ausweichen nicht mit altem I-Anteil weiterfahren
                    continue

                img = stream.read()
                if img is None:
                    logger.warning("Noch kein Kamerabild verfügbar.")
                    continue

                detection = collector.peek_detection(img)
                if detection is not None and detection.confidence >= DETECTION_CONFIDENCE_MIN:
                    logger.info("Müll erkannt (%s, %.0f%%). Übernehme Sammlung.",
                                detection.class_name, detection.confidence * 100)
                    collector.reset()
                    collector.run_until_collected()
                    steering_pid.reset()
                    continue

                curve = getLaneCurve(img, display=0)
                # curve entspricht bereits dem Regelfehler (Sollwert 0 = Fahrzeug mittig)
                steering = steering_pid.update(curve)
                motor.move(LANE_FOLLOW_SPEED, steering, t=dt)

        except KeyboardInterrupt:
            logger.info("Abbruch durch Benutzer.")
        finally:
            motor.stop()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
