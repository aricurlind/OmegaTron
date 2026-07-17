from unittest.mock import MagicMock, patch

from Detection_Modul import State, WasteCollector
from Obj_Detection import Detection


def _make_detection(center_x: float, frame_width: int = 320) -> Detection:
    x = int(center_x) - 20
    return Detection(class_id=0, class_name="Bio_Muell", confidence=0.9, x=x, y=50, w=40, h=40)


def _make_collector() -> WasteCollector:
    # capture/sensors werden injiziert, damit der Konstruktor keine echte
    # Kamera oder serielle Verbindung öffnet.
    return WasteCollector(capture=MagicMock(), sensors=MagicMock())


def test_centering_offset_zero_when_object_is_centered():
    detection = _make_detection(center_x=160)
    assert WasteCollector.centering_offset(detection, frame_width=320) == 0


def test_centering_offset_negative_when_object_left_of_center():
    detection = _make_detection(center_x=100)
    assert WasteCollector.centering_offset(detection, frame_width=320) < 0


def test_centering_offset_positive_when_object_right_of_center():
    detection = _make_detection(center_x=220)
    assert WasteCollector.centering_offset(detection, frame_width=320) > 0


@patch("Detection_Modul.motor")
def test_centering_transitions_to_approaching_once_within_tolerance(mock_motor):
    collector = _make_collector()
    collector._state = State.ZENTRIEREN
    detection = _make_detection(center_x=160)  # exakt mittig

    collector._step_centering(detection, frame_width=320)

    assert collector._state == State.ANNAEHERN
    mock_motor.move.assert_not_called()


@patch("Detection_Modul.motor")
def test_centering_steers_toward_object_when_off_center(mock_motor):
    collector = _make_collector()
    collector._state = State.ZENTRIEREN
    detection = _make_detection(center_x=250)  # rechts von der Mitte

    collector._step_centering(detection, frame_width=320)

    assert collector._state == State.ZENTRIEREN
    mock_motor.move.assert_called_once()
    steering = mock_motor.move.call_args.args[1]
    assert steering > 0  # Objekt ist rechts -> nach rechts lenken


@patch("Detection_Modul.motor")
def test_centering_falls_back_to_searching_without_detection(mock_motor):
    collector = _make_collector()
    collector._state = State.ZENTRIEREN

    collector._step_centering(None, frame_width=320)

    assert collector._state == State.SUCHEN
    mock_motor.move.assert_not_called()


@patch("Detection_Modul.motor")
def test_approaching_switches_to_grabbing_within_grab_distance(mock_motor):
    collector = _make_collector()
    collector._state = State.ANNAEHERN
    detection = _make_detection(center_x=160)

    collector._step_approaching(detection, frame_width=320, distance_cm=5.0)

    assert collector._state == State.GREIFEN
    mock_motor.stop.assert_called_once()


@patch("Detection_Modul.motor")
def test_approaching_drives_forward_when_still_far(mock_motor):
    collector = _make_collector()
    collector._state = State.ANNAEHERN
    detection = _make_detection(center_x=160)

    collector._step_approaching(detection, frame_width=320, distance_cm=100.0)

    assert collector._state == State.ANNAEHERN
    mock_motor.move.assert_called_once()


@patch("Detection_Modul.arm")
def test_grabbing_retries_on_hardware_error_then_succeeds(mock_arm):
    collector = _make_collector()
    # Erster Versuch schlägt fehl (z. B. I2C-Wackelkontakt), zweiter klappt.
    mock_arm.Roboterarm.side_effect = [OSError("I2C error"), None, None, None]

    detection = _make_detection(center_x=160)
    result = collector._step_grabbing(detection)

    assert result is True


@patch("Detection_Modul.arm")
def test_grabbing_gives_up_after_max_attempts(mock_arm):
    collector = _make_collector()
    mock_arm.Roboterarm.side_effect = OSError("I2C error")

    detection = _make_detection(center_x=160)
    result = collector._step_grabbing(detection)

    assert result is False
