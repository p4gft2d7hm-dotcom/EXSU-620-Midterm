"""
code.py  -  runs on the Raspberry Pi Pico 2 W (CircuitPython 9).

Copy to the CIRCUITPY drive together with turnlogic.py.
Needs in CIRCUITPY/lib:  adafruit_lsm6ds, adafruit_register, adafruit_bus_device, neopixel.mpy

Wiring
    LSM6DS3TR-C  ->  Grove I2C0 port   (SDA = GP8, SCL = GP9)
    NeoPixel DIN ->  GP16              (power from 3V3 and GND)
    PAM8302 A+   ->  GP18              (A- to GND, Vin to 3V3)
    Button       ->  GP20 and GND
"""
import json
import time

import board
import busio
import digitalio
import neopixel
import pwmio
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC

from turnlogic import Config, Monitor, Stillness, angles

cfg = Config()
cfg.TIME_SCALE = 1.0        # set to 60.0 for a demo: 2 hours pass in 2 minutes

SAMPLE_HZ = 20
ALPHA = 0.15                # low-pass filter weight for each new sample
VOLUME = 6000               # PWM duty, 0 to 32768. Also use the trim pot on the amp

COLOURS = {
    "normal": (0, 60, 0),
    "advisory": (90, 45, 0),
    "critical": (120, 0, 0),
    "technical": (0, 60, 70),
}

# (frequency Hz, on seconds, off seconds) and how often the pattern repeats
PATTERNS = {
    "advisory": ([(880, 0.20, 0.20)] * 3, 30.0),
    "critical": ([(1200, 0.15, 0.10)] * 10, 5.0),
    "technical": ([(600, 0.08, 0.0), (900, 0.08, 0.0)], 20.0),
}

# ------------------------------------------------------------------ hardware
pixels = neopixel.NeoPixel(board.GP16, 16, brightness=0.2, auto_write=False)
speaker = pwmio.PWMOut(board.GP18, frequency=440, duty_cycle=0, variable_frequency=True)
button = digitalio.DigitalInOut(board.GP20)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

i2c = busio.I2C(scl=board.GP9, sda=board.GP8)
sensor = None


def connect_sensor():
    global sensor
    try:
        sensor = LSM6DS3TRC(i2c)
    except Exception:
        sensor = None


class Beeper:
    """Plays tone patterns without blocking the main loop."""

    def __init__(self):
        self.steps = []
        self.i = 0
        self.t_next = 0.0
        self.sounding = False
        self.repeat = 0.0
        self.t_repeat = 0.0
        self.name = None

    def set(self, name, now):
        if name == self.name:
            return
        self.name = name
        speaker.duty_cycle = 0
        self.sounding = False
        if name in PATTERNS:
            self.steps, self.repeat = PATTERNS[name]
            self.i = 0
            self.t_next = now
            self.t_repeat = now + self.repeat
        else:
            self.steps = []

    def tick(self, now):
        if not self.steps:
            return
        if self.i >= len(self.steps):
            if now >= self.t_repeat:
                self.i = 0
                self.t_next = now
                self.t_repeat = now + self.repeat
            return
        if now < self.t_next:
            return
        freq, on_s, off_s = self.steps[self.i]
        if not self.sounding:
            speaker.frequency = freq
            speaker.duty_cycle = VOLUME
            self.sounding = True
            self.t_next = now + on_s
        else:
            speaker.duty_cycle = 0
            self.sounding = False
            self.t_next = now + off_s
            self.i += 1


def show(state):
    pixels.fill(COLOURS[state])
    pixels.show()


# ---------------------------------------------------------------------- main
connect_sensor()
monitor = Monitor(cfg)
still = Stillness(cfg)
beeper = Beeper()

fx = fy = fz = None
sum_x = sum_y = sum_z = 0.0
n_sum = 0
events_out = []
last_state = None
last_button = True
period = 1.0 / SAMPLE_HZ
t_prev = time.monotonic()
t_report = t_prev
t_retry = t_prev
roll = pitch = 0.0
still_value = None

while True:
    now = time.monotonic()
    dt = now - t_prev
    t_prev = now

    # ---- read the sensor
    ok = False
    if sensor is None:
        if now - t_retry > 2.0:
            t_retry = now
            connect_sensor()
    else:
        try:
            ax, ay, az = sensor.acceleration
            ok = True
        except Exception:
            sensor = None

    if ok:
        if fx is None:
            fx, fy, fz = ax, ay, az
        fx += ALPHA * (ax - fx)
        fy += ALPHA * (ay - fy)
        fz += ALPHA * (az - fz)
        roll, pitch = angles(fx, fy, fz, cfg.ROLL_SIGN)
        sum_x += ax
        sum_y += ay
        sum_z += az
        n_sum += 1
        g = (fx * fx + fy * fy + fz * fz) ** 0.5
        if g < cfg.G_MIN or g > cfg.G_MAX:
            ok = False      # implausible gravity counts as a sensor fault

    # ---- acknowledge button (pressed = low)
    pressed = not button.value
    ack = pressed and not last_button
    last_button = pressed

    # ---- logic
    is_still = still_value is not None and still_value < cfg.STILL_RANGE
    events_out += monitor.update(dt, roll, pitch, sensor_ok=ok, still=is_still, ack=ack)

    # ---- indicator and sound
    state = monitor.display_state()
    if state != last_state:
        show(state)
        last_state = state
    silenced = state == "critical" and monitor.acked
    beeper.set(None if (state == "normal" or silenced) else state, now)
    beeper.tick(now)

    # ---- one line of JSON per second to the laptop
    if now - t_report >= 1.0:
        t_report = now
        if n_sum:
            still.add(sum_x / n_sum, sum_y / n_sum, sum_z / n_sum)
            still_value = still.metric()
        sum_x = sum_y = sum_z = 0.0
        n_sum = 0
        print(json.dumps({
            "roll": round(roll, 1),
            "pitch": round(pitch, 1),
            "pos": monitor.pos,
            "state": state,
            "acked": monitor.acked,
            "remaining_s": round(monitor.remaining(), 1),
            "interval_s": round(monitor.interval, 1),
            "still": None if still_value is None else round(still_value, 4),
            "ok": ok,
            "ev": events_out,
        }))
        events_out = []

    # ---- hold the sample rate
    spare = period - (time.monotonic() - now)
    if spare > 0:
        time.sleep(spare)
