"""
server.py  -  laptop service for the repositioning patch.

Reads one JSON line per second from the Pico over USB, stores it in SQLite,
and serves the dashboard and the REST endpoints.

    python server.py --port COM5              (Windows)
    python server.py --port /dev/tty.usbmodem1101   (Mac)
    python server.py --simulate               (no hardware, 2 hours pass in 2 minutes)

Dashboard:  http://localhost:8000
Phone:      http://<laptop IP address>:8000  on the same Wi-Fi
"""
import argparse
import json
import os
import sqlite3
import threading
import time
import urllib.request
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import notify

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "patch.db")
SHIFT_STARTS = [7, 15, 23]                  # hours of the day when a shift begins

app = FastAPI(title="Repositioning patch")
latest = {"t": 0.0, "data": None}
sim = {"on": False, "ack": False, "turn": False}   # the simulator has no bedside button


# ------------------------------------------------------------------ database
def db():
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("""CREATE TABLE IF NOT EXISTS samples(
            ts REAL, roll REAL, pitch REAL, pos TEXT, state TEXT,
            remaining_s REAL, still REAL)""")
        con.execute("CREATE TABLE IF NOT EXISTS events(ts REAL, type TEXT, detail TEXT)")
        con.execute("CREATE INDEX IF NOT EXISTS i_samples ON samples(ts)")
        con.execute("CREATE INDEX IF NOT EXISTS i_events ON events(ts)")
        notify.init(con)


def store(msg):
    """Save one message from the patch."""
    now = time.time()
    latest["t"] = now
    latest["data"] = msg
    with db() as con:
        con.execute("INSERT INTO samples VALUES(?,?,?,?,?,?,?)",
                    (now, msg.get("roll"), msg.get("pitch"), msg.get("pos"),
                     msg.get("state"), msg.get("remaining_s"), msg.get("still")))
        for name, detail in msg.get("ev", []):
            con.execute("INSERT INTO events VALUES(?,?,?)", (now, name, detail))
            if name in ("advisory", "critical", "technical"):
                push(name)


def push(name):
    """Send an alert to every registered, consenting recipient (see notify.py).
    Runs in the background so a slow network never delays the patch data."""
    event_ts = time.time()

    def send():
        try:
            with db() as con:
                notify.dispatch(con, name, event_ts)
        except Exception as e:
            print("notification problem:", e)
    threading.Thread(target=send, daemon=True).start()


# -------------------------------------------------------------------- inputs
def read_serial(port):
    import serial
    while True:
        try:
            with serial.Serial(port, 115200, timeout=2) as ser:
                print("reading from", port)
                while True:
                    line = ser.readline().decode("utf-8", "ignore").strip()
                    if line.startswith("{"):
                        try:
                            store(json.loads(line))
                        except ValueError:
                            pass
        except Exception as e:
            print("serial problem:", e, "- retrying in 2 s")
            time.sleep(2)


def simulate():
    """Plays a scripted patient through the same logic the Pico runs."""
    from turnlogic import Config, Monitor
    cfg = Config()
    cfg.TIME_SCALE = 60.0
    cfg.BENCH_MODE = True
    m = Monitor(cfg)
    # (seconds, roll, pitch)
    script = [(40, 0, 2), (15, 8, 2), (30, 0, 2), (60, 42, 3), (20, 38, 3),
              (5, 5, 3), (150, 4, 3), (30, -40, 2), (40, 0, 78), (60, -35, 2)]
    print("simulating: 2 hours pass in 2 minutes")
    manual_roll = manual_left = shown_roll = 0
    while True:
        for seconds, script_roll, script_pitch in script:
            for _ in range(seconds):
                # the Turn patient button moves the patient for 20 s, then the script resumes
                if sim["turn"]:
                    sim["turn"] = False
                    manual_roll = 0 if abs(shown_roll) > 20 else 40
                    manual_left = 20
                if manual_left > 0:
                    manual_left -= 1
                    roll, pitch = manual_roll, 2
                else:
                    roll, pitch = script_roll, script_pitch
                shown_roll = roll
                events = []
                for _ in range(20):
                    events += m.update(0.05, roll, pitch, ack=sim["ack"])
                    sim["ack"] = False
                store({"roll": roll, "pitch": pitch, "pos": m.pos,
                       "state": m.display_state(), "acked": m.acked,
                       "remaining_s": round(m.remaining(), 1),
                       "interval_s": m.interval, "still": 0.2, "ok": True,
                       "bench_mode": cfg.BENCH_MODE,
                       "expired_intervals": m.expired_intervals,
                       "ev": events})
                time.sleep(1)


# --------------------------------------------------------------------- shift
def shift_start(now=None):
    now = now or datetime.now()
    starts = [now.replace(hour=h, minute=0, second=0, microsecond=0) for h in SHIFT_STARTS]
    starts += [s - timedelta(days=1) for s in starts]
    return max(s for s in starts if s <= now)


def shift_summary():
    start = shift_start()
    t0 = start.timestamp()
    with db() as con:
        events = con.execute("SELECT type FROM events WHERE ts>=? ORDER BY ts", (t0,)).fetchall()
        upright = con.execute("SELECT COUNT(*) FROM samples WHERE ts>=? AND pos='upright'",
                              (t0,)).fetchone()[0]
    on_time = late = partial = turns = 0
    audited_expiries = 0
    pending = False
    for (name,) in events:
        if name == "interval_expired":
            audited_expiries += 1
        if name == "critical":
            late += 1
            pending = True
        elif name == "turn":
            turns += 1
            if pending:
                pending = False
            else:
                on_time += 1
        elif name == "partial":
            partial += 1
    intervals = on_time + late
    return {
        "shift_start": start.strftime("%H:%M"),
        "turns": turns,
        "late_intervals": late,
        "audited_expiries": audited_expiries,
        "audit_basis": "receipt-time shift; full elapsed intervals since effective turn",
        "partial_turns": partial,
        "compliance_pct": None if intervals == 0 else round(100.0 * on_time / intervals),
        "out_of_bed_min": round(upright / 60.0, 1),   # one sample per second
    }


# ----------------------------------------------------------------- endpoints
@app.get("/")
def dashboard():
    return FileResponse(os.path.join(HERE, "dashboard.html"))


@app.get("/api/status")
def status():
    with db() as con:
        ev = con.execute("SELECT ts,type,detail FROM events ORDER BY ts DESC LIMIT 15").fetchall()
    return {
        "simulated": sim["on"],
        "age_s": None if latest["data"] is None else round(time.time() - latest["t"], 1),
        "latest": latest["data"],
        "shift": shift_summary(),
        "events": [dict(e) for e in ev],
    }


@app.post("/api/ack")
def ack():
    """Stands in for the bedside button. Only works in simulation."""
    if sim["on"]:
        sim["ack"] = True
    return {"accepted": sim["on"]}


@app.post("/api/turn")
def turn():
    """Turns the simulated patient. Only works in simulation."""
    if sim["on"]:
        sim["turn"] = True
    return {"accepted": sim["on"]}


@app.get("/api/history")
def history(minutes: float = 10):
    t0 = time.time() - minutes * 60
    with db() as con:
        rows = con.execute("SELECT ts,roll,pitch,pos,state FROM samples WHERE ts>=? ORDER BY ts",
                           (t0,)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/shift")
def shift():
    return shift_summary()


@app.get("/api/events")
def events(limit: int = 200):
    with db() as con:
        rows = con.execute("SELECT ts,type,detail FROM events ORDER BY ts DESC LIMIT ?",
                           (limit,)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- recipients
class Registration(BaseModel):
    name: str
    channel: str
    address: str
    apikey: str = ""
    consent: bool = False


@app.get("/api/consent")
def consent_text():
    return {"version": notify.CONSENT_VERSION, "text": notify.CONSENT_TEXT}


@app.get("/api/recipients")
def recipients():
    with db() as con:
        return notify.listing(con)


@app.post("/api/recipients")
def add_recipient(r: Registration):
    try:
        with db() as con:
            rid = notify.register(con, r.name, r.channel, r.address, r.consent, r.apikey)
    except notify.RegistrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": rid}


@app.post("/api/recipients/{rid}/withdraw")
def withdraw_recipient(rid: int):
    with db() as con:
        if not notify.withdraw(con, rid):
            raise HTTPException(status_code=404, detail="no active recipient with that id")
    return {"withdrawn": rid}


@app.post("/api/recipients/{rid}/test")
def test_recipient(rid: int):
    """Send the fixed test text to one active recipient and log it like an alert."""
    with db() as con:
        rec = con.execute("SELECT * FROM recipients WHERE id=? AND withdrawn_ts IS NULL",
                          (rid,)).fetchone()
        if rec is None:
            raise HTTPException(status_code=404, detail="no active recipient with that id")
        t0 = time.time()
        ok, detail = notify.http_send(rec, notify.TEXTS["test"])
        done = time.time()
        con.execute("INSERT INTO deliveries(recipient_id,event,event_ts,sent_ts,latency_s,ok,detail)"
                    " VALUES(?,?,?,?,?,?,?)", (rid, "test", t0, done, round(done - t0, 3),
                                               1 if ok else 0, detail[:300]))
    return {"ok": ok, "detail": detail}


@app.get("/api/deliveries")
def delivery_log(limit: int = 100):
    with db() as con:
        return notify.deliveries(con, limit)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", help="serial port of the Pico, for example COM5")
    p.add_argument("--simulate", action="store_true", help="run without hardware")
    p.add_argument("--http", type=int, default=8000)
    args = p.parse_args()
    if not args.port and not args.simulate:
        p.error("give --port or --simulate")
    if os.environ.get("NTFY_TOPIC"):
        print("NTFY_TOPIC is no longer used. Register recipients on the dashboard instead.")
    init_db()
    sim["on"] = args.simulate
    target = simulate if args.simulate else lambda: read_serial(args.port)
    threading.Thread(target=target, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=args.http, log_level="warning")
