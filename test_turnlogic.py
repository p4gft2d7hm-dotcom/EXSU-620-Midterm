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


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("pass ", t.__name__)
    print("%d tests passed" % len(tests))
