"""Gemeinsame Test-Konfiguration.

Das Projekt verwendet (wie auf dem Raspberry Pi deployt) flache Imports
zwischen den Modulordnern statt eines installierbaren Packages - deshalb
müssen die Ordner hier genauso wie in main.py von Hand zum sys.path
hinzugefügt werden.

RPi.GPIO und cv2 sind auf einem normalen Entwicklungs-PC nicht (sinnvoll)
installierbar bzw. hier bewusst nicht vorausgesetzt. Für die Tests werden
sie durch MagicMock ersetzt, damit die reine Logik (PID, Filter, State
Machine, Mixing-Mathematik) ohne echte Hardware bzw. Kamera getestet werden
kann. Tests, die tatsächliches Bildverarbeitungsverhalten von OpenCV
prüfen würden, gehören nicht in diese Suite, sondern auf die Zielhardware.
"""

import os
import sys
from unittest.mock import MagicMock

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TESTS_DIR)

for _subfolder in ("Common", "Motorsteuerung", "Hindernisumfahrung", "Objekterkennung",
                    "Roboterarm", "Fahrspurerkennung/AlgorithmusOhneDL",
                    "Fahrspurerkennung/Datensammlung"):
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, _subfolder))

if "RPi" not in sys.modules:
    _fake_gpio = MagicMock()
    _fake_rpi = MagicMock()
    _fake_rpi.GPIO = _fake_gpio
    sys.modules["RPi"] = _fake_rpi
    sys.modules["RPi.GPIO"] = _fake_gpio

if "cv2" not in sys.modules:
    sys.modules["cv2"] = MagicMock()
