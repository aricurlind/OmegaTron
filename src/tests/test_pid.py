from pid import PIDController, PIDGains


def test_first_update_returns_pure_proportional_term():
    # Beim ersten Aufruf ist dt=0 (kein vorheriger Zeitstempel), daher
    # dürfen weder I- noch D-Anteil einfließen.
    pid = PIDController(PIDGains(kp=0.5), output_limits=(-10.0, 10.0))
    output = pid.update(2.0, now=0.0)
    assert output == 1.0


def test_output_is_clamped_to_limits():
    pid = PIDController(PIDGains(kp=10.0), output_limits=(-1.0, 1.0))
    output = pid.update(5.0, now=0.0)
    assert output == 1.0

    output = pid.update(-5.0, now=1.0)
    assert output == -1.0


def test_integral_term_accumulates_over_time():
    pid = PIDController(PIDGains(kp=0.0, ki=2.0), output_limits=(-10.0, 10.0))
    pid.update(1.0, now=0.0)  # dt=0 -> keine Akkumulation
    output = pid.update(1.0, now=1.0)  # dt=1s -> integral = 1*1 = 1
    assert output == 2.0


def test_derivative_term_reacts_to_error_change():
    pid = PIDController(PIDGains(kp=0.0, kd=1.0), output_limits=(-10.0, 10.0))
    pid.update(0.0, now=0.0)
    output = pid.update(2.0, now=1.0)  # dt=1s -> d = (2-0)/1 = 2
    assert output == 2.0


def test_reset_clears_integral_and_derivative_state():
    pid = PIDController(PIDGains(kp=0.0, ki=1.0), output_limits=(-10.0, 10.0))
    pid.update(5.0, now=0.0)
    pid.update(5.0, now=1.0)  # baut Integralanteil auf
    pid.reset()

    # Nach reset() ist prev_time wieder None, der nächste Aufruf muss sich
    # also wie ein allererster Aufruf verhalten (dt=0, kein I-Sprung).
    output = pid.update(5.0, now=100.0)
    assert output == 0.0


def test_anti_windup_keeps_integral_within_configured_limits():
    pid = PIDController(PIDGains(kp=0.0, ki=1.0), output_limits=(-1.0, 1.0),
                         integral_limits=(-0.5, 0.5))
    output = 0.0
    for t in range(1, 20):
        output = pid.update(10.0, now=float(t))
    # Ohne Anti-Windup würde der Integralanteil unbegrenzt anwachsen; mit
    # Clamping sättigt er an integral_limits (hier 0.5), nicht erst an der
    # äußeren output_limits-Grenze (hier 1.0).
    assert output == 0.5
