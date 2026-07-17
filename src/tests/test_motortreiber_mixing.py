from Motortreiber import mix_differential_drive


def test_straight_ahead_has_no_steering_bias():
    left, right = mix_differential_drive(0.5, 0.0)
    assert left == right == 0.5


def test_steering_right_slows_left_side_relative_to_right():
    left, right = mix_differential_drive(0.5, 0.3)
    assert left < right


def test_steering_left_slows_right_side_relative_to_left():
    left, right = mix_differential_drive(0.5, -0.3)
    assert right < left


def test_output_never_exceeds_unit_range():
    left, right = mix_differential_drive(1.0, 1.0)
    assert -1.0 <= left <= 1.0
    assert -1.0 <= right <= 1.0


def test_inputs_outside_unit_range_are_clamped_first():
    left_a, right_a = mix_differential_drive(2.0, 0.0)
    left_b, right_b = mix_differential_drive(1.0, 0.0)
    assert (left_a, right_a) == (left_b, right_b)
