# Omega-Tron – Autonomes Roboterauto

## Projektstruktur

```
OmegaTron/
├── main.py                       # Verbindet Fahrspurfolge, Hindernisumfahrung und Müllsammlung
├── requirements.txt               # Laufzeit-Abhängigkeiten (Pi)
├── requirements-dev.txt           # + pytest für Entwicklung/Tests auf einem PC
├── Common/
│   ├── config.py                 # Zentrale Konfiguration (Schwellwerte, Regler-Gains)
│   ├── pid.py                    # Generischer PID-Regler mit Anti-Windup
│   ├── filters.py                # Median- und Kalman-Filter für Sensordaten
│   └── video_stream.py           # Threaded Kamera + feste Regelschleifen-Taktung
├── tests/                        # pytest-Suite mit gemockter Hardware (RPi.GPIO, cv2)
│   ├── conftest.py
│   ├── test_pid.py
│   ├── test_filters.py
│   ├── test_ultraschallsensoren.py
│   ├── test_motortreiber_mixing.py
│   └── test_waste_collector.py
│
├── Motorsteuerung/
│   ├── AMSpi.py                  # Open-Source Bibliothek für Arduino Motor Shield L293D
│   ├── Motortreiber.py           # Fahrbefehle (vorwärts, rückwärts, links, rechts, ...)
│   └── hand.py                   # Manuelle Tastatursteuerung via Pygame
│
├── Hindernisumfahrung/
│   ├── USS_Master.py             # Raspberry Pi Master – liest serielle USS-Daten und steuert Motoren
│   └── USS_5.ino                 # Arduino Nano Slave – liest 5 Ultraschallsensoren
│
├── Fahrspurerkennung/
│   ├── AlgorithmusOhneDL/
│   │   ├── LaneDetection.py      # Hauptskript – Fahrspurerkennung ohne Deep Learning
│   │   ├── Hilfsfunktionen.py    # HSV-Filter, Warping, Histogramm, Visualisierung
│   │   └── Farbengenerator.py    # Tool zum Einstellen der HSV-Grenzwerte
│   │
│   ├── Datensammlung/
│   │   ├── LogMain.py            # Hauptskript – Bilder + Lenkwerte aufzeichnen (PS4-Controller)
│   │   ├── LogModul.py           # Speichert Bilder und CSV-Log
│   │   └── KameraModul.py        # Kamera-Wrapper
│   │
│   ├── Training/
│   │   ├── Training.py           # CNN-Training nach NVIDIA-Architektur
│   │   └── Hilf_Func.py          # Datenladen, Augmentation, Preprocessing, Modell, Generator
│   │
│   └── MitDL/
│       └── Omega_Tron_CNN_Main.py  # Autonome Fahrt mit trainiertem CNN-Modell
│
├── Objekterkennung/
│   ├── Obj_Detection.py          # YOLOv3-Erkennung + Bounding Box Anzeige
│   ├── Detection_Modul.py        # Schnittstelle Kamera → Erkennung → Roboterarm
│   └── train_yolov3_custom.py    # YOLOv3-Training in Google Colab (kommentiert)
│
└── Roboterarm/
    ├── Adafruit_PCA9685.py       # PWM-Controller-Bibliothek für PCA9685
    └── ModulRoboterarm_aktuell.py  # Roboterarm-Steuerung (Start, Greifen, Wegwerfen)
```

## Hardware

- Raspberry Pi 4B (Master)
- Arduino Nano (Slave – Ultraschallsensoren)
- Arduino Motor Shield L293D
- 4x DC-Motoren
- 5x Ultraschallsensoren (USS)
- Raspberry Pi Kamera
- PCA9685 PWM-Controller
- 4-DOF Roboterarm mit Servos
- PS4-Controller (für manuelle Steuerung / Datensammlung)

## Erkannte Objektklassen

| ID | Klasse            |
|----|-------------------|
| 0  | Bio-Müll          |
| 1  | Metallische Dose  |
| 2  | Papier            |
| 3  | Karton/Schachtel  |
| 4  | Plastik           |

## Regelung, Filterung & Nebenläufigkeit

- **PID statt Bang-Bang**: Fahrspurlenkung (main.py) und Objektzentrierung
  (Detection_Modul.py) verwenden `Common/pid.py` statt fester
  Geschwindigkeit "Richtung Fehler". Gains sind Startwerte und müssen am
  Fahrzeug getunt werden.
- **Sensorfilterung**: Jeder Ultraschallsensor läuft durch einen eigenen
  Medianfilter (`Common/filters.py`), der einzelne Fehlmessungen abfängt.
  Ein Kalman-Filter für ein 1D-Konstantwert-Modell steht ebenfalls bereit.
- **Feste Zykluszeit**: `Common/video_stream.py` entkoppelt die
  Kameraaufnahme (Hintergrundthread) von der Regelschleife und taktet
  Letztere über `FixedRateLoop` auf eine feste Frequenz, da die PID-Regler
  eine konsistente dt erwarten.
- **Recovery-Verhalten**: `Ultraschallsensoren.py` versucht bei
  Verbindungsabbruch einen Reconnect statt abzustürzen;
  `Detection_Modul.py` wiederholt die Greifsequenz bei einem I2C-Fehler,
  bevor sie aufgibt.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

Hardwareabhängige Module (RPi.GPIO, cv2) werden in `tests/conftest.py`
gemockt, damit die reine Logik (PID, Filter, Decodierschema, Mixing-Mathematik,
State Machine) ohne Pi/Kamera/Arduino läuft.

## ML-Training

`Fahrspurerkennung/Training/` nutzt inzwischen einen echten
Train/Val/Test-Split, Dropout/BatchNorm, EarlyStopping und
ReduceLROnPlateau. Jeder Lauf legt unter `runs/<timestamp>/` sein Modell,
den Trainingsverlauf (`history.csv`) und die verwendeten Hyperparameter
(`config.json`) ab – kein vollwertiges Experiment-Tracking wie MLflow/W&B,
aber genug, um Läufe nachvollziehen zu können.

