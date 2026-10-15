"""
turnlogic.py  -  position, turn and alarm logic for the repositioning patch.

Pure Python. The same file runs on the Pico (CircuitPython) and on the laptop,
so the logic can be tested without hardware.

Axis convention (set by the keyed cradle):
    sensor Y points to the patient's head
    sensor Z points out of the chest
    sensor X points across the chest
"""
import math


class Config:
    # ---- turn definition (CR-3). Defend these two numbers with evidence. ----
    TURN_ANGLE_DEG = 30.0      # minimum roll change from the last resting angle
    DWELL_S = 120.0            # the new angle must be held this long
    TURN_HYST_DEG = 5.0        # candidate cancels only below TURN_ANGLE - this

    # ---- repositioning interval (CR-2) ----
    INTERVAL_S = 7200.0        # 2 hours
    ADVISORY_LEAD_S = 900.0    # advisory 15 minutes before expiry

    # ---- position classes (CR-1), with hysteresis so labels do not flicker ----
    LATERAL_ENTER_DEG = 30.0
    LATERAL_EXIT_DEG = 20.0
    UPRIGHT_ENTER_DEG = 60.0
    UPRIGHT_EXIT_DEG = 50.0
    ROLL_SIGN = 1.0            # set to -1.0 if left and right come out swapped

    # ---- technical alarm ----
    STILL_WINDOW_S = 30        # seconds of history used for the stillness check
    STILL_RANGE = 0.03         # m/s^2. Below this the patch is not on a breathing chest
    G_MIN = 8.8                # plausible gravity magnitude, m/s^2
    G_MAX = 10.8
    FAULT_HOLD_S = 5.0         # a fault must persist this long before it alarms

    # ---- demo ----
    TIME_SCALE = 1.0           # 60 makes 2 hours pass in 2 minutes


def angles(ax, ay, az, roll_sign=1.0):
    """Return (roll, pitch) in degrees from one acceleration reading.
    roll  : rotation about the head-to-foot axis. 0 = supine, +90 = right side.
    pitch : how upright the torso is. 0 = lying flat, 90 = upright."""
    g = math.sqrt(ax * ax + ay * ay + az * az)
    if g < 1e-6:
        return 0.0, 0.0
    s = max(-1.0, min(1.0, ay / g))
    pitch = math.degrees(math.asin(s))
    roll = roll_sign * math.degrees(math.atan2(ax, az))
    return roll, pitch


def wrap(deg):
    """Wrap an angle difference into -180..180."""
    while deg > 180.0:
        deg -= 360.0
    while deg < -180.0:
        deg += 360.0
    return deg


class Stillness:
    """Tracks one-second means of each axis. If none of the axes has moved by
    more than STILL_RANGE over the window, nobody is breathing under the patch."""

    def __init__(self, cfg):
        self.n = int(cfg.STILL_WINDOW_S)
        self.buf = []

    def add(self, mx, my, mz):
        self.buf.append((mx, my, mz))
        if len(self.buf) > self.n:
            self.buf.pop(0)

    def metric(self):
        """Largest range across the three axes, m/s^2. None until the window fills."""
        if len(self.buf) < self.n:
            return None
        worst = 0.0
        for i in range(3):
            vals = [s[i] for s in self.buf]
            r = max(vals) - min(vals)
            if r > worst:
                worst = r
        return worst


class Monitor:
    """Feed it roll and pitch. It returns events and keeps the alarm state."""

    def __init__(self, cfg=None):
        self.cfg = cfg or Config()
        k = float(self.cfg.TIME_SCALE)
        self.dwell = self.cfg.DWELL_S / k
        self.interval = self.cfg.INTERVAL_S / k
        self.lead = self.cfg.ADVISORY_LEAD_S / k

        self.pos = "supine"
        self.anchor = None          # roll at the last effective turn
        self.since_turn = 0.0       # seconds since the last effective turn
        self.cand_t = 0.0           # how long the current candidate turn has held
        self.upright_t = 0.0
        self.upright_counted = False

        self.alarm = "normal"       # normal | advisory | critical
        self.acked = False
        self.turned_since_critical = False
        self.technical = False
        self.fault_t = 0.0
        self.turns = 0

    # ---------------------------------------------------------------- position
    def _classify(self, roll, pitch):
        c = self.cfg
        if self.pos == "upright":
            if pitch >= c.UPRIGHT_EXIT_DEG:
                return "upright"
        elif pitch >= c.UPRIGHT_ENTER_DEG:
            return "upright"
        side = "right" if roll > 0 else "left"
        if abs(roll) >= c.LATERAL_ENTER_DEG:
            return side
        if self.pos == side and abs(roll) > c.LATERAL_EXIT_DEG:
            return side
        return "supine"

    # -------------------------------------------------------------------- turn
    def _turn(self, ev, kind, roll):
        self.turns += 1
        self.since_turn = 0.0
        self.cand_t = 0.0
        self.anchor = roll
        ev.append(("turn", kind))
        if self.alarm == "advisory":
            self.alarm = "normal"
        elif self.alarm == "critical":
            self.turned_since_critical = True

    # ------------------------------------------------------------------ update
    def update(self, dt, roll, pitch, sensor_ok=True, still=False, ack=False):
        """Call at a fixed rate. Returns a list of (event, detail) tuples."""
        c = self.cfg
        ev = []

        # technical alarm: sensor fault or a patch that is not on a patient
        if (not sensor_ok) or still:
            self.fault_t += dt
        else:
            self.fault_t = 0.0
        tech = self.fault_t >= c.FAULT_HOLD_S
        if tech != self.technical:
            self.technical = tech
            reason = "sensor" if not sensor_ok else "motionless"
            ev.append(("technical", reason) if tech else ("technical_clear", ""))

        if sensor_ok:
            if self.anchor is None:
                self.anchor = roll
            new_pos = self._classify(roll, pitch)
            if new_pos != self.pos:
                ev.append(("position", new_pos))
                self.pos = new_pos

            if self.pos == "upright":
                self.cand_t = 0.0
                self.upright_t += dt
                if not self.upright_counted and self.upright_t >= self.dwell:
                    self.upright_counted = True
                    self._turn(ev, "upright", self.anchor)
            else:
                if self.upright_counted:
                    # back in bed: the clock restarts from the new resting angle
                    self.anchor = roll
                    self.since_turn = 0.0
                self.upright_t = 0.0
                self.upright_counted = False

                delta = abs(wrap(roll - self.anchor))
                if delta >= c.TURN_ANGLE_DEG:
                    self.cand_t += dt
                    if self.cand_t >= self.dwell:
                        self._turn(ev, "lateral", roll)
                elif self.cand_t > 0.0:
                    if delta >= c.TURN_ANGLE_DEG - c.TURN_HYST_DEG:
                        self.cand_t += dt
                    else:
                        ev.append(("partial", "%.0f s" % self.cand_t))
                        self.cand_t = 0.0

        # the clock holds at zero while the patient is counted as out of bed
        if not (self.pos == "upright" and self.upright_counted):
            self.since_turn += dt

        # alarm state machine (Figure 3)
        remaining = self.interval - self.since_turn
        if self.alarm == "normal" and remaining <= self.lead:
            self.alarm = "advisory"
            ev.append(("advisory", ""))
        if self.alarm in ("normal", "advisory") and remaining <= 0.0:
            self.alarm = "critical"
            self.acked = False
            self.turned_since_critical = False
            ev.append(("critical", ""))
        if self.alarm == "critical":
            if ack and not self.acked:
                self.acked = True
                ev.append(("ack", ""))
            if self.acked and self.turned_since_critical:
                self.alarm = "normal"
                ev.append(("critical_clear", ""))
        return ev

    # ----------------------------------------------------------------- outputs
    def display_state(self):
        """What the indicator shows. Critical outranks technical."""
        if self.alarm == "critical":
            return "critical"
        if self.technical:
            return "technical"
        return self.alarm

    def remaining(self):
        return self.interval - self.since_turn
