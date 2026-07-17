"""Speichert Kamerabilder und eine CSV-Protokolldatei mit Bildname und Lenkwinkel."""

import os
from datetime import datetime
from typing import List

import cv2
import pandas as pd

BASE_DIRECTORY: str = os.path.join(os.getcwd(), "DataCollected")

_img_list: List[str] = []
_steering_list: List[float] = []
_folder_index: int = 0
_session_path: str = ""


def _create_session_folder() -> str:
    global _folder_index
    while os.path.exists(os.path.join(BASE_DIRECTORY, f"IMG{_folder_index}")):
        _folder_index += 1
    path = os.path.join(BASE_DIRECTORY, f"IMG{_folder_index}")
    os.makedirs(path)
    return path


_session_path = _create_session_folder()


def saveData(img, steering: float) -> None:
    """Speichert ein Bild und den zugehörigen Lenkwinkel im aktuellen Session-Ordner."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file_name = os.path.join(_session_path, f"Image_{timestamp}.jpg")
    cv2.imwrite(file_name, img)
    _img_list.append(file_name)
    _steering_list.append(steering)


def saveLog() -> None:
    """Schreibt die gesammelten Bildpfade und Lenkwinkel als CSV-Datei."""
    raw_data = {"Image": _img_list, "Steering": _steering_list}
    df = pd.DataFrame(raw_data)
    df.to_csv(os.path.join(BASE_DIRECTORY, f"log_{_folder_index}.csv"), index=False, header=False)
    print("Log gespeichert.")
    print("Anzahl Bilder:", len(_img_list))


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    for _ in range(10):
        success, frame = cap.read()
        if not success:
            break
        saveData(frame, 0.5)
        cv2.imshow("Image", frame)
        cv2.waitKey(1)
    saveLog()
