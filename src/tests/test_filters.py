from filters import KalmanFilter1D, MedianFilter


def test_median_filter_suppresses_single_outlier():
    f = MedianFilter(window_size=3)
    f.update(10.0)
    f.update(10.0)
    result = f.update(500.0)  # z. B. ein USS-Timeout-Wert
    assert result == 10.0


def test_median_filter_tracks_sustained_change():
    f = MedianFilter(window_size=3)
    result = None
    for _ in range(3):
        result = f.update(50.0)
    assert result == 50.0


def test_median_filter_rejects_invalid_window_size():
    try:
        MedianFilter(window_size=0)
        assert False, "erwartete ValueError für window_size=0"
    except ValueError:
        pass


def test_kalman_filter_converges_to_constant_measurement():
    kf = KalmanFilter1D(process_variance=1e-2, measurement_variance=4.0, initial_estimate=0.0)
    estimate = 0.0
    for _ in range(200):
        estimate = kf.update(30.0)
    assert abs(estimate - 30.0) < 0.5


def test_kalman_filter_smooths_single_spike():
    kf = KalmanFilter1D(process_variance=1e-2, measurement_variance=4.0, initial_estimate=20.0, initial_error=0.1)
    estimate = kf.update(200.0)  # einzelner Ausreißer
    # Der Schätzwert darf sich nicht sofort auf den Ausreißer setzen.
    assert estimate < 100.0
