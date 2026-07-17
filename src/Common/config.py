"""Zentrale Konfiguration für Omega-Tron.

Vorher waren Schwellwerte und Regler-Parameter als Modulkonstanten über das
gesamte Projekt verteilt (z. B. GRAB_DISTANCE_CM in Detection_Modul.py,
SAFETY_DISTANCE_CM in main.py). Das machte es unnötig aufwändig, das
Verhalten für einen Testlauf anzupassen, ohne mehrere Dateien zu bearbeiten.

Diese Datei bündelt die Werte, die für main.py, Detection_Modul.py und
Ultraschallsensoren.py relevant sind, als Dataclasses. Andere Module
(Motorsteuerung, Fahrspurerkennung/Training) behalten vorerst ihre eigenen
lokalen Konstanten, da sie eigenständig genutzt werden und eine vollständige
Migration den Rahmen dieser Überarbeitung sprengen würde.
"""

from dataclasses import dataclass, field

from pid import PIDGains  # noqa: E402  (Pfad wird von main.py vor dem Import ergänzt)


@dataclass
class UltrasonicConfig:
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout_s: float = 1.0
    median_filter_window: int = 5
    reconnect_delay_s: float = 2.0
    max_reconnect_attempts: int = 5


@dataclass
class SafetyConfig:
    obstacle_distance_cm: float = 25.0


@dataclass
class LaneFollowConfig:
    speed: float = 0.5
    steering_gains: PIDGains = field(default_factory=lambda: PIDGains(kp=0.8, ki=0.05, kd=0.15))


@dataclass
class WasteCollectorConfig:
    center_tolerance_px: int = 25
    grab_distance_cm: float = 15.0
    search_turn_speed: float = 0.3
    approach_speed: float = 0.25
    detection_confidence_min: float = 0.6
    centering_gains: PIDGains = field(default_factory=lambda: PIDGains(kp=0.006, ki=0.0002, kd=0.002))
    grab_max_attempts: int = 2


@dataclass
class ControlLoopConfig:
    frequency_hz: float = 10.0


@dataclass
class OmegaTronConfig:
    camera_index: int = 0
    ultrasonic: UltrasonicConfig = field(default_factory=UltrasonicConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    lane_follow: LaneFollowConfig = field(default_factory=LaneFollowConfig)
    waste_collector: WasteCollectorConfig = field(default_factory=WasteCollectorConfig)
    control_loop: ControlLoopConfig = field(default_factory=ControlLoopConfig)


DEFAULT_CONFIG = OmegaTronConfig()
