from Ultraschallsensoren import OFFSET_STEP, decode_raw_value


def test_decode_front_sensor():
    assert decode_raw_value(42.0) == {"vorne": 42.0}


def test_decode_second_sensor_with_offset():
    assert decode_raw_value(OFFSET_STEP + 10.0) == {"vorne_rechts": 10.0}


def test_decode_last_sensor():
    assert decode_raw_value(4 * OFFSET_STEP + 5.0) == {"links": 5.0}


def test_decode_rejects_out_of_range_values():
    assert decode_raw_value(5 * OFFSET_STEP + 1.0) is None
    assert decode_raw_value(-1.0) is None
