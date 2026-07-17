"""Verknüpft Kameraerkennung, Ultraschallsensorik und Roboterarm.

Neu gegenüber dem Originalprojekt: Die reine Objekterkennung reichte nicht
aus, um Müll zuverlässig zu greifen, da weder die Ausrichtung des Fahrzeugs
zum Objekt noch der tatsächliche Abstand berücksichtigt wurden. Dieses Modul
schließt die Lücke, indem es die Kameraerkennung mit dem vorderen
Ultraschallsensor koppelt:

  1. SUCHEN     – kein Objekt im Bild: langsame Drehung, bis eines erkannt wird.
  2. ZENTRIEREN – Objekt erkannt, aber nicht mittig im Bild: PID-geregelte
                  seitliche Korrekturbewegung, bis der Objektmittelpunkt
                  innerhalb der Toleranz um die Bildmitte liegt (entspricht
                  "Müll in die Mitte der Fahrspur bringen").
  3. ANNAEHERN  – Objekt zentriert, aber Ultraschall-Distanz noch zu groß:
                  langsam geradeaus fahren, Zentrierung läuft weiter mit.
  4. GREIFEN    – Ultraschall-Distanz im Greifbereich: anhalten und die
                  Greifsequenz des Roboterarms auslösen (mit Retry, falls
                  eine I2C-Schreiboperation fehlschlägt).

Die Zentrierung wurde zunächst mit fester Geschwindigkeit "Richtung Fehler"
umgesetzt (Bang-Bang). Das führte bei kleinem Versatz zu Überschwingen und
bei großem zu langsamer Reaktion; ein PID-Regler behebt das.
"""

import logging
import sys
from enum import Enum, auto
from typing import Optional

import cv2

sys.path.append("../Common")
from pid import PIDController, PIDGains  # noqa: E402

import ModulRoboterarm_aktuell as arm
import Motortreiber as motor
from Obj_Detection import Detection, detect_objects, most_confident
from Ultraschallsensoren import UltrasonicArray

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH: str = "yolov3_custom.cfg"
WEIGHT_PATH: str = "yolov3_custom_final.weights"
YOLO_INPUT_SIZE: int = 320

CENTER_TOLERANCE_PX: int = 25
CENTERING_GAINS = PIDGains(kp=0.006, ki=0.0002, kd=0.002)
APPROACH_SPEED: float = 0.25
GRAB_DISTANCE_CM: float = 15.0
SEARCH_TURN_SPEED: float = 0.3
COMMAND_DURATION_S: float = 0.15
GRAB_MAX_ATTEMPTS: int = 2

USS_PORT: str = "/dev/ttyUSB0"
FRONT_SENSOR_NAME: str = "vorne"

CLASS_LABELS_DE = {
    "Bio_Muell": "Bio-Müll",
    "Metallische_Dose": "Metallische Dose",
    "Papier": "Papier",
    "Karton_Schachtel": "Karton/Schachtel",
    "Plastik": "Plastik",
}


class State(Enum):
    SUCHEN = auto()
    ZENTRIEREN = auto()
    ANNAEHERN = auto()
    GREIFEN = auto()


def _load_network(config_path: str, weight_path: str) -> cv2.dnn_Net:
    net = cv2.dnn.readNetFromDarknet(config_path, weight_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net


def _run_inference(net: cv2.dnn_Net, img) -> list:
    blob = cv2.dnn.blobFromImage(img, 1 / 255, (YOLO_INPUT_SIZE, YOLO_INPUT_SIZE), [0, 0, 0], 1, crop=False)
    net.setInput(blob)
    layer_names = net.getLayerNames()
    output_names = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    return net.forward(output_names)


class WasteCollector:
    """State machine, die Kamera- und Ultraschalldaten zum Einsammeln von Müll fusioniert."""

    def __init__(self, camera_index: int = 0, uss_port: str = USS_PORT,
                 capture: Optional[cv2.VideoCapture] = None,
                 sensors: Optional[UltrasonicArray] = None) -> None:
        """
        :param capture: Bereits geöffnete Kamera, die z. B. auch von der
            Fahrspurerkennung genutzt wird. Wird nur eine eigene Kamera
            geöffnet, wenn hier None übergeben wird (Standalone-Betrieb).
        :param sensors: Bereits initialisiertes UltrasonicArray. Wird nur
            eine eigene serielle Verbindung geöffnet, wenn hier None
            übergeben wird.
        """
        self._cap = capture if capture is not None else cv2.VideoCapture(camera_index)
        self._owns_capture = capture is None
        self._net = _load_network(CONFIG_PATH, WEIGHT_PATH)
        self._sensors = sensors if sensors is not None else UltrasonicArray(port=uss_port)
        self._owns_sensors = sensors is None
        self._state = State.SUCHEN
        self._centering_pid = PIDController(CENTERING_GAINS, output_limits=(-1.0, 1.0))

    def close(self) -> None:
        if self._owns_capture:
            self._cap.release()
        if self._owns_sensors:
            self._sensors.close()
        cv2.destroyAllWindows()

    def __enter__(self) -> "WasteCollector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _best_detection(self, img) -> Optional[Detection]:
        outputs = _run_inference(self._net, img)
        detections = detect_objects(outputs, img, YOLO_INPUT_SIZE)
        return most_confident(detections)

    def peek_detection(self, img) -> Optional[Detection]:
        """Prüft ein bereits eingelesenes Bild auf Müll, ohne den internen State zu ändern.

        Für main.py gedacht, um zu entscheiden, ob die Kontrolle an
        run_until_collected() übergeben werden soll.
        """
        return self._best_detection(img)

    def reset(self) -> None:
        """Setzt die State Machine (und den PID-Zustand) auf SUCHEN zurück."""
        self._state = State.SUCHEN
        self._centering_pid.reset()

    @staticmethod
    def centering_offset(detection: Detection, frame_width: int) -> int:
        """Horizontaler Versatz des Objekts zur Bildmitte in Pixeln (negativ = links).

        Als staticmethod ausgelagert, damit sie ohne Kamera/YOLO/Sensorik
        instanziiert und getestet werden kann.
        """
        return detection.center_x - frame_width // 2

    def _step_searching(self, detection: Optional[Detection]) -> None:
        if detection is not None:
            logger.info("Objekt gefunden: %s", CLASS_LABELS_DE.get(detection.class_name, detection.class_name))
            self._state = State.ZENTRIEREN
            self._centering_pid.reset()
            return
        motor.move(0.0, SEARCH_TURN_SPEED, t=COMMAND_DURATION_S)

    def _step_centering(self, detection: Optional[Detection], frame_width: int) -> None:
        if detection is None:
            self._state = State.SUCHEN
            return

        offset = self.centering_offset(detection, frame_width)
        if abs(offset) <= CENTER_TOLERANCE_PX:
            logger.info("Objekt zentriert (Versatz %s px). Nähere mich an.", offset)
            self._state = State.ANNAEHERN
            return

        steering = self._centering_pid.update(float(offset))
        motor.move(0.0, steering, t=COMMAND_DURATION_S)

    def _step_approaching(self, detection: Optional[Detection], frame_width: int, distance_cm: float) -> None:
        if detection is None:
            self._state = State.SUCHEN
            return

        offset = self.centering_offset(detection, frame_width)
        if abs(offset) > CENTER_TOLERANCE_PX:
            self._state = State.ZENTRIEREN
            return

        if distance_cm <= GRAB_DISTANCE_CM:
            logger.info("Greifabstand erreicht (%.1f cm).", distance_cm)
            motor.stop()
            self._state = State.GREIFEN
            return

        # Zentrierung läuft während der Annäherung mit, damit seitlicher
        # Versatz durch Bodenunebenheiten sofort korrigiert wird.
        steering = self._centering_pid.update(float(offset))
        motor.move(APPROACH_SPEED, steering, t=COMMAND_DURATION_S)

    def _step_grabbing(self, detection: Optional[Detection]) -> bool:
        name = CLASS_LABELS_DE.get(detection.class_name, "Objekt") if detection else "Objekt"

        for attempt in range(1, GRAB_MAX_ATTEMPTS + 1):
            try:
                logger.info("%s wird gegriffen (Versuch %s/%s).", name, attempt, GRAB_MAX_ATTEMPTS)
                arm.Roboterarm("Start")
                arm.Roboterarm("Greifen")
                logger.info("%s wird entsorgt.", name)
                arm.Roboterarm("Wegwerfen")
                logger.info("%s wurde entsorgt.", name)
                return True
            except OSError as exc:
                # I2C-Schreiboperationen (PCA9685) können bei Wackelkontakt
                # oder Spannungseinbruch unter Last fehlschlagen. Es gibt
                # keine Sensorrückmeldung, ob der Greifer wirklich etwas
                # gefasst hat - im Zweifel wird die Sequenz wiederholt statt
                # stillschweigend weiterzumachen.
                logger.warning("Greifsequenz fehlgeschlagen (%s). Versuch %s/%s.", exc, attempt, GRAB_MAX_ATTEMPTS)

        logger.error("Greifen von %s nach %s Versuchen aufgegeben.", name, GRAB_MAX_ATTEMPTS)
        return False

    def run_once(self) -> bool:
        """Führt einen Erkennungs-/Steuerzyklus aus.

        :return: True, sobald ein Objekt erfolgreich eingesammelt wurde.
        """
        success, img = self._cap.read()
        if not success:
            logger.warning("Kein Kamerabild erhalten.")
            return False

        detection = self._best_detection(img)
        distances = self._sensors.poll()
        distance_cm = distances[FRONT_SENSOR_NAME]

        cv2.imshow("Objekt Erkennung Kamera", img)
        cv2.waitKey(1)

        if self._state == State.SUCHEN:
            self._step_searching(detection)
        elif self._state == State.ZENTRIEREN:
            self._step_centering(detection, img.shape[1])
        elif self._state == State.ANNAEHERN:
            self._step_approaching(detection, img.shape[1], distance_cm)
        elif self._state == State.GREIFEN:
            collected = self._step_grabbing(detection)
            motor.stop()
            self._state = State.SUCHEN
            self._centering_pid.reset()
            return collected

        return False

    def run_until_collected(self) -> None:
        while not self.run_once():
            pass


if __name__ == "__main__":
    with WasteCollector() as collector:
        collector.run_until_collected()
