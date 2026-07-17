"""Hilfsfunktionen für das CNN-Training: Datenladen, Augmentation, Modell, Generator."""

import os
import random
from typing import List, Tuple

import cv2
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imgaug import augmenters as iaa
from sklearn.utils import shuffle
from tensorflow.keras.layers import BatchNormalization, Convolution2D, Dense, Dropout, Flatten
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

LOG_FILE_COUNT: int = 4
CROP_TOP: int = 54
CROP_BOTTOM: int = 120
CNN_INPUT_SIZE: Tuple[int, int] = (200, 66)
LEARNING_RATE: float = 0.0001
DROPOUT_RATE: float = 0.3


# 1 – Initialisierung

def getName(file_path: str) -> str:
    parts = file_path.split("/")[-2:]
    return os.path.join(parts[0], parts[1])


def importDataInfo(path: str) -> pd.DataFrame:
    columns = ["Center", "Steering"]
    frames = []
    for x in range(LOG_FILE_COUNT):
        data_new = pd.read_csv(os.path.join(path, f"log_{x}.csv"), names=columns)
        print(f"{x}:{data_new.shape[0]} ", end="")
        data_new["Center"] = data_new["Center"].apply(getName)
        frames.append(data_new)
    data = pd.concat(frames, ignore_index=True)
    print(" ")
    print("Anzahl Dateien:", data.shape[0])
    return data


# 2 – Visualisierung

def balanceData(data: pd.DataFrame, display: bool = True) -> pd.DataFrame:
    n_bins = 31
    samples_per_bin = 300
    hist, bins = np.histogram(data["Steering"], n_bins)
    center = (bins[:-1] + bins[1:]) * 0.5

    if display:
        plt.bar(center, hist, width=0.03)
        plt.plot((np.min(data["Steering"]), np.max(data["Steering"])), (samples_per_bin, samples_per_bin))
        plt.title("Data Plot")
        plt.xlabel("Lenkungswinkel")
        plt.ylabel("Anzahl der Trainingsdaten")
        plt.show()

    remove_index_list: List[int] = []
    steering_values = data["Steering"].to_numpy()
    for j in range(n_bins):
        bin_data_list = [i for i in range(len(steering_values))
                          if bins[j] <= steering_values[i] <= bins[j + 1]]
        bin_data_list = shuffle(bin_data_list)
        remove_index_list.extend(bin_data_list[samples_per_bin:])

    print("Entfernte Bilder:", len(remove_index_list))
    data = data.drop(data.index[remove_index_list])
    print("Verbleibende Bilder:", len(data))

    if display:
        hist, _ = np.histogram(data["Steering"], n_bins)
        plt.bar(center, hist, width=0.03)
        plt.plot((np.min(data["Steering"]), np.max(data["Steering"])), (samples_per_bin, samples_per_bin))
        plt.title("Balanced Data")
        plt.xlabel("Lenkungswinkel")
        plt.ylabel("Anzahl der übrigen Daten")
        plt.show()
    return data


# 3 – Laden der Daten

def loadData(path: str, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    images_path = [os.path.join(path, data.iloc[i, 0]) for i in range(len(data))]
    steering = [float(data.iloc[i, 1]) for i in range(len(data))]
    return np.asarray(images_path), np.asarray(steering)


# 4 – Augmentation

def augmentImage(img_path: str, steering: float) -> Tuple[np.ndarray, float]:
    img = mpimg.imread(img_path)
    if np.random.rand() < 0.5:
        pan = iaa.Affine(translate_percent={"x": (-0.1, 0.1), "y": (-0.1, 0.1)})
        img = pan.augment_image(img)
    if np.random.rand() < 0.5:
        zoom = iaa.Affine(scale=(1, 1.2))
        img = zoom.augment_image(img)
    if np.random.rand() < 0.5:
        brightness = iaa.Multiply((0.5, 1.2))
        img = brightness.augment_image(img)
    if np.random.rand() < 0.5:
        img = cv2.flip(img, 1)
        steering = -steering
    return img, steering


# 5 – Preprocessing

def preProcess(img: np.ndarray) -> np.ndarray:
    img = img[CROP_TOP:CROP_BOTTOM, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, CNN_INPUT_SIZE)
    return img / 255


# 6 – CNN-Modell (NVIDIA-Architektur, erweitert um BatchNorm/Dropout)

def createModel(dropout_rate: float = DROPOUT_RATE) -> Sequential:
    """Baut das CNN nach NVIDIA-Vorbild, ergänzt um Regularisierung.

    Das Originalmodell hatte keinerlei Regularisierung, obwohl die
    Datensammlung nur wenige hundert Bilder pro Fahrsituation liefert -
    ein klassisches Rezept für Overfitting auf die Trainingsstrecke.
    BatchNorm stabilisiert das Training zusätzlich bei den eher kleinen
    Batch-Größen (100 in Training.py).
    """
    model = Sequential()
    model.add(Convolution2D(24, (5, 5), (2, 2), input_shape=(66, 200, 3), activation="elu"))
    model.add(BatchNormalization())
    model.add(Convolution2D(36, (5, 5), (2, 2), activation="elu"))
    model.add(BatchNormalization())
    model.add(Convolution2D(48, (5, 5), (2, 2), activation="elu"))
    model.add(Convolution2D(64, (3, 3), activation="elu"))
    model.add(Convolution2D(64, (3, 3), activation="elu"))
    model.add(Flatten())
    model.add(Dropout(dropout_rate))
    # model.add(Dropout(0.8))  # deutlich zu hoch angesetzt, Loss ist nicht mehr gesunken
    model.add(Dense(100, activation="elu"))
    model.add(Dense(50, activation="elu"))
    model.add(Dense(10, activation="elu"))
    model.add(Dense(1))
    model.compile(Adam(learning_rate=LEARNING_RATE), loss="mse", metrics=["mae"])
    return model


# 7 – Datengenerator

def dataGen(images_path: np.ndarray, steering_list: np.ndarray, batch_size: int, train_flag: bool):
    while True:
        img_batch, steering_batch = [], []
        for _ in range(batch_size):
            index = random.randint(0, len(images_path) - 1)
            if train_flag:
                img, steering = augmentImage(images_path[index], steering_list[index])
            else:
                img = mpimg.imread(images_path[index])
                steering = steering_list[index]
            img_batch.append(preProcess(img))
            steering_batch.append(steering)
        yield np.asarray(img_batch), np.asarray(steering_batch)
