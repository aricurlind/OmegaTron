"""YOLOv3-Ausgabeauswertung: filtert Detektionen und zeichnet Bounding Boxes."""

from typing import List, NamedTuple, Optional

import cv2
import numpy as np

CONFIDENCE_THRESHOLD: float = 0.5
NMS_THRESHOLD: float = 0.1

CLASS_NAMES: List[str] = [
    "Bio_Muell",
    "Metallische_Dose",
    "Papier",
    "Karton_Schachtel",
    "Plastik",
]


class Detection(NamedTuple):
    """Eine einzelne, nach NMS gefilterte Objekterkennung."""
    class_id: int
    class_name: str
    confidence: float
    x: int
    y: int
    w: int
    h: int

    @property
    def center_x(self) -> int:
        return self.x + self.w // 2

    @property
    def center_y(self) -> int:
        return self.y + self.h // 2


def detect_objects(outputs, img: np.ndarray, input_size: int) -> List[Detection]:
    """Wertet die YOLO-Netzwerkausgaben aus, wendet NMS an und zeichnet die Treffer ein.

    :param outputs: Rohausgaben von net.forward(outputNames).
    :param img: Kamerabild (BGR); wird zur Visualisierung direkt beschriftet.
    :param input_size: Kantenlänge des quadratischen YOLO-Eingabebilds (z. B. 320).
    :return: Liste aller erkannten Objekte nach Non-Maximum-Suppression.
    """
    height, width = img.shape[:2]
    boxes, class_ids, confidences = [], [], []

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = int(np.argmax(scores))
            confidence = float(scores[class_id])
            if confidence <= CONFIDENCE_THRESHOLD:
                continue
            w, h = int(detection[2] * input_size), int(detection[3] * input_size)
            x = int((detection[0] * input_size) - w / 2)
            y = int((detection[1] * input_size) - h / 2)
            boxes.append([x, y, w, h])
            class_ids.append(class_id)
            confidences.append(confidence)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
    indices = np.array(indices).flatten() if len(indices) else []

    detections: List[Detection] = []
    for i in indices:
        x, y, w, h = boxes[i]
        detection = Detection(class_ids[i], CLASS_NAMES[class_ids[i]], confidences[i], x, y, w, h)
        detections.append(detection)
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 2)
        cv2.putText(img, f"{detection.class_name.upper()} {int(detection.confidence * 100)}%",
                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

    return detections


def most_confident(detections: List[Detection]) -> Optional[Detection]:
    """Liefert die Detektion mit der höchsten Konfidenz, falls vorhanden."""
    return max(detections, key=lambda d: d.confidence) if detections else None
