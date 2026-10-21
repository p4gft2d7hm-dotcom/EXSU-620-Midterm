"""
test_turnlogic.py  -  runs the scripted protocol against the turn logic on the laptop.
Run with:  python test_turnlogic.py
"""
from turnlogic import Config, Monitor


def run(script, cfg=None, dt=0.05, ack_at=None):
    """script is a list of (seconds, roll, pitch). Returns [(time, event, detail)]."""
    m = Monitor(cfg or Config())
    t = 0.0
    log = []
    for seconds, roll, pitch in script:
        for _ in range(int(seconds / dt)):
            ack = ack_at is not None and abs(t - ack_at) < dt / 2
            for name, detail in m.update(dt, roll, pitch, ack=ack):
                log.append((round(t), name, detail))
            t += dt
    return m, log


def names(log):
    return [e[1] for e in log]


def test_small_shift_is_not_a_turn():
    m, log = run([(600, 0, 0), (600, 8, 0), (600, 0, 0)])
    assert m.turns == 0, log


def test_held_turn_counts():
    m, log = run([(600, 0, 0), (300, 35, 0)])
    assert m.turns == 1 and m.pos == "right", log
    assert m.since_turn < 200


def test_brief_turn_is_partial():
    m, log = run([(600, 0, 0), (60, 40, 0), (600, 0, 0)])
    assert m.turns == 0 and "partial" in names(log), log


def test_creeping_shifts_count_once_they_reach_the_angle():
    m, log = run([(300, 0, 0), (300, 10, 0), (300, 20, 0), (300, 32, 0)])
    assert m.turns == 1, log


def test_advisory_then_critical_then_latch():
    # no turn for 2 h, then a real turn at 2 h 10, acknowledge at 2 h 20
    m, log = run([(7800, 0, 0), (1200, -45, 0)], dt=0.5, ack_at=8400)
    n = names(log)
    adv = [e[0] for e in log if e[1] == "advisory"][0]
    crit = [e[0] for e in log if e[1] == "critical"][0]
    assert abs(adv - 6300) <= 1 and abs(crit - 7200) <= 1, log
    turn = [e[0] for e in log if e[1] == "turn"][0]
    clear = [e[0] for e in log if e[1] == "critical_clear"][0]
    assert turn < clear and abs(clear - 8400) <= 1, log   # stays latched until acknowledged
    assert m.alarm == "normal"


def test_turn_during_advisory_returns_to_normal():
    m, log = run([(6600, 0, 0), (300, 40, 0)], dt=0.5)
    assert "advisory" in names(log) and m.alarm == "normal", log


def test_out_of_bed_counts_and_holds_the_clock():
    m, log = run([(600, 0, 0), (1800, 0, 80), (60, 0, 0)])
    assert m.turns == 1 and m.since_turn < 100, log


def test_motionless_patch_raises_technical():
    m = Monitor(Config())
    for _ in range(200):
        m.update(0.05, 0, 0, still=True)
    assert m.display_state() == "technical"


def feed(m, seconds, roll, pitch=0, **kwargs):
    events = []
    for _ in range(int(seconds * 20)):
        events += m.update(0.05, roll, pitch, **kwargs)
    return events


def test_hysteresis_band_pauses_without_qualifying_time():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 60, 35)
    qualified_before = m.cand_t
    feed(m, 200, 27)
    assert abs(m.cand_t - qualified_before) < 0.001
    feed(m, 1, 35)
    assert m.turns == 0
    feed(m, 120, 35)
    assert m.turns == 1


def test_sensor_gap_cannot_join_two_half_turns():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 60, 40)
    feed(m, 600, 40, sensor_ok=False)
    feed(m, 61, 40)
    assert m.turns == 0
    feed(m, 61, 40)
    assert m.turns == 1


def test_opposite_sides_do_not_share_dwell():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 60, 40)
    feed(m, 61, -40)
    assert m.turns == 0
    feed(m, 60, -40)
    assert m.turns == 1


def test_stationary_phantom_turn_counts_despite_technical_flag():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 300, 40, still=True)
    assert m.turns == 1 and m.technical


def test_noise_near_threshold_does_not_flood_partial_events():
    import math
    for mean, amplitude, anchor in [(31, 1, 0.8), (33, 1.5, 0.8)]:
        m = Monitor()
        feed(m, 1, anchor)
        events = []
        for i in range(300 * 20):
            roll = mean + amplitude * math.sin(2 * math.pi * i / 20)
            events += m.update(0.05, roll, 0)
        assert m.turns == 1, (mean, amplitude, events)
        assert sum(name == 'partial' for name, _ in events) <= 1, events


def test_below_hysteresis_release_resets_dwell():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 60, 40)
    feed(m, 1, 24)
    feed(m, 61, 40)
    assert m.turns == 0


def test_hysteresis_band_cannot_start_or_complete_turn():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 200, 27)
    assert m.turns == 0 and m.cand_t == 0
    feed(m, 1, 35)
    feed(m, 300, 27)
    assert m.turns == 0 and m.cand_t < 2


def test_invalid_upright_resumes_overdue_clock():
    m = Monitor()
    feed(m, 1, 0)
    feed(m, 121, 0, 80)
    assert m.upright_counted
    feed(m, 10, 0, 80, sensor_ok=False)
    assert not m.upright_counted and m.since_turn > 9


def test_bench_mode_allows_phantom_without_stillness_alarm():
    cfg = Config()
    cfg.BENCH_MODE = True
    m = Monitor(cfg)
    feed(m, 1, 0, still=True)
    feed(m, 300, 40, still=True)
    assert m.turns == 1 and not m.technical


def test_bench_mode_keeps_sensor_fault_alarm_and_resets_dwell():
    cfg = Config()
    cfg.BENCH_MODE = True
    m = Monitor(cfg)
    feed(m, 1, 0)
    feed(m, 60, 40)
    feed(m, 6, 40, sensor_ok=False, still=True)
    assert m.technical and m.cand_t == 0
    feed(m, 61, 40)
    assert m.turns == 0


def test_expiry_audit_continues_while_alarm_latched_after_turn():
    m = Monitor()
    events = []
    for _ in range(7201):
        events += m.update(1, 0, 0)
    assert m.expired_intervals == 1 and m.alarm == 'critical'
    events += feed(m, 121, 40)
    assert m.turns == 1 and m.alarm == 'critical' and not m.acked
    for _ in range(7201):
        events += m.update(1, 40, 0)
    assert m.expired_intervals == 2
    assert sum(name == 'interval_expired' for name, _ in events) == 2
    assert sum(name == 'critical' for name, _ in events) == 1


def test_expiry_audit_reports_each_full_interval_once():
    m = Monitor()
    events = []
    for _ in range(21601):
        events += m.update(1, 0, 0)
    assert m.expired_intervals == 3
    assert [detail for name, detail in events if name == 'interval_expired'] == [
        'elapsed_s=7200.000', 'elapsed_s=14400.000', 'elapsed_s=21600.000']
    assert not any(name == 'interval_expired' for name, _ in m.update(1, 0, 0))


def test_early_turn_resets_audit_deadline():
    m = Monitor()
    for _ in range(7000):
        m.update(1, 0, 0)
    feed(m, 121, 40)
    assert m.turns == 1
    for _ in range(1000):
        m.update(1, 40, 0)
    assert m.expired_intervals == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("pass ", t.__name__)
    print("%d tests passed" % len(tests))

