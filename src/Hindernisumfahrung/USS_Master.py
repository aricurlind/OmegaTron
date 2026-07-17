"""Raspberry-Pi-Master: liest die USS-Sensoren und steuert die Hindernisumfahrung."""

import logging

import Motortreiber as m
from Ultraschallsensoren import UltrasonicArray

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def choose_maneuver(distances: dict) -> None:
    """Wählt anhand der fünf Sensordistanzen das passende Ausweichmanöver."""
    vorne = distances["vorne"]
    vorne_rechts = distances["vorne_rechts"]
    vorne_links = distances["vorne_links"]
    rechts = distances["rechts"]
    links = distances["links"]

    if vorne < min(vorne_rechts, vorne_links, rechts, links):
        m.sharpLeft() if vorne_rechts < vorne_links else m.sharpRight()
    elif vorne_rechts < min(vorne, vorne_links, rechts, links):
        m.swiftForwardLeft()
    elif vorne_links < min(vorne, vorne_rechts, rechts, links):
        m.swiftForwardRight()
    elif rechts < min(vorne, vorne_links, vorne_rechts, links):
        m.swiftForwardLeft()
    elif links < min(vorne, vorne_links, rechts, vorne_rechts):
        m.swiftForwardRight()
    else:
        m.moveForward()


def main() -> None:
    with UltrasonicArray(port="/dev/ttyUSB0") as sensors:
        while True:
            distances = sensors.poll()
            logger.info("Sensordistanzen: %s", distances)
            choose_maneuver(distances)


if __name__ == "__main__":
    main()
