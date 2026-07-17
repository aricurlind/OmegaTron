"""Autonome Fahrspurfolge mit dem trainierten CNN-Modell (NVIDIA-Architektur)."""

from typing import Final

import cv2
import numpy as np
from tensorflow import keras

import KameraModul as kM
import Motortreiber as m

MODEL_PATH: str = "/home/pi/Fahrspurerkennung/CNN_Code/Model_CNN.h5"
STEERING_SENSITIVITY: Final = 0.9
MAX_SPEED: Final = 0.8
CROP_TOP: Final = 54
CROP_BOTTOM: Final = 120
CNN_INPUT_SIZE: Final = (200, 66)


def preprocess(img: np.ndarray) -> np.ndarray:
    """Bereitet ein Kamerabild identisch zum Trainingsvorverarbeitungsschritt auf."""
    img = img[CROP_TOP:CROP_BOTTOM, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, CNN_INPUT_SIZE)
    return img / 255


def main() -> None:
    model = keras.models.load_model(MODEL_PATH)
    model.summary()

    while True:
        img = kM.getImg(True, size=(240, 120))
        img = preprocess(np.asarray(img))
        steering = float(model.predict(np.array([img]), verbose=0))
        m.move(MAX_SPEED, -steering * STEERING_SENSITIVITY, t=0.1)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()
