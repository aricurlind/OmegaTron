"""Trainiert das Fahrspur-CNN (NVIDIA-Architektur) auf gesammelten Daten.

Erweiterungen gegenüber der ersten Fassung:
  - Echter 3-Wege-Split (Train/Val/Test) statt nur Train/Val, damit das
    Testergebnis nicht durch die Modellauswahl während des Trainings
    (die auf dem Val-Set beobachtet wird) optimistisch verzerrt ist.
  - EarlyStopping + ReduceLROnPlateau statt einer festen Epochenzahl.
  - Ein CSVLogger pro Lauf plus eine JSON-Datei mit den verwendeten
    Hyperparametern - kein vollwertiges Experiment-Tracking wie MLflow/W&B,
    aber genug, um spätere Trainingsläufe nachvollziehen zu können.
"""

import json
import os
from datetime import datetime

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import CSVLogger, EarlyStopping, ReduceLROnPlateau

from Hilf_Func import DROPOUT_RATE, LEARNING_RATE, balanceData, createModel, dataGen, importDataInfo, loadData

DATA_PATH: str = "Data_Log"
VAL_SPLIT: float = 0.2
TEST_SPLIT: float = 0.1
RANDOM_STATE: int = 10
STEPS_PER_EPOCH: int = 100
VALIDATION_STEPS: int = 50
MAX_EPOCHS: int = 60
EARLY_STOPPING_PATIENCE: int = 8
LR_PATIENCE: int = 4
MODEL_OUTPUT_PATH: str = "Model_CNN.h5"
RUNS_DIR: str = "runs"


def _new_run_dir() -> str:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def _update_run_config(run_dir: str, **hyperparameters) -> None:
    """Schreibt/ergänzt config.json für den Lauf.

    Wird zweimal aufgerufen (vor und nach dem Training) - deshalb wird eine
    bestehende Datei eingelesen und gemergt statt überschrieben. Ein
    einfaches json.dump(..., "w") hätte beim zweiten Aufruf die vorher
    gespeicherten Hyperparameter überschrieben.
    """
    path = os.path.join(run_dir, "config.json")
    existing = {}
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)
    existing.update(hyperparameters)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def main() -> None:
    run_dir = _new_run_dir()

    data = importDataInfo(DATA_PATH)
    print(data.head())

    data = balanceData(data, display=True)
    images_path, steerings = loadData(DATA_PATH, data)

    # Erst Test-Set abspalten, danach den Rest in Train/Val - so bleibt der
    # Testanteil während der gesamten Modellentwicklung unberührt.
    x_trainval, x_test, y_trainval, y_test = train_test_split(
        images_path, steerings, test_size=TEST_SPLIT, random_state=RANDOM_STATE)
    x_train, x_val, y_train, y_val = train_test_split(
        x_trainval, y_trainval, test_size=VAL_SPLIT, random_state=RANDOM_STATE)

    print("Training Bilder Gesamt:", len(x_train))
    print("Validierung Bilder Gesamt:", len(x_val))
    print("Test Bilder Gesamt:", len(x_test))

    model = createModel(dropout_rate=DROPOUT_RATE)

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=EARLY_STOPPING_PATIENCE, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=LR_PATIENCE, min_lr=1e-6),
        CSVLogger(os.path.join(run_dir, "history.csv")),
    ]

    _update_run_config(
        run_dir,
        learning_rate=LEARNING_RATE,
        dropout_rate=DROPOUT_RATE,
        max_epochs=MAX_EPOCHS,
        early_stopping_patience=EARLY_STOPPING_PATIENCE,
        lr_patience=LR_PATIENCE,
        train_samples=len(x_train),
        val_samples=len(x_val),
        test_samples=len(x_test),
        random_state=RANDOM_STATE,
    )

    history = model.fit(
        dataGen(x_train, y_train, 100, True),
        steps_per_epoch=STEPS_PER_EPOCH,
        epochs=MAX_EPOCHS,
        validation_data=dataGen(x_val, y_val, 50, False),
        validation_steps=VALIDATION_STEPS,
        callbacks=callbacks,
    )

    test_loss, test_mae = model.evaluate(dataGen(x_test, y_test, 50, False), steps=VALIDATION_STEPS)
    print(f"Test-Loss (MSE): {test_loss:.4f}, Test-MAE: {test_mae:.4f}")
    _update_run_config(
        run_dir,
        test_loss=float(test_loss),
        test_mae=float(test_mae),
        epochs_trained=len(history.history["loss"]),
    )

    model_path = os.path.join(run_dir, MODEL_OUTPUT_PATH)
    model.save(model_path)
    print("Modell gespeichert:", model_path)

    plt.plot(history.history["loss"])
    plt.plot(history.history["val_loss"])
    plt.legend(["Training", "Validiert"])
    plt.title("Loss")
    plt.xlabel("Epoch")
    plt.savefig(os.path.join(run_dir, "loss.png"))
    plt.show()


if __name__ == "__main__":
    main()
