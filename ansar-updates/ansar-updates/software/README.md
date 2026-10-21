# Project 08 - local development package

This is an unpublished local copy based on GitHub commit bee302bf67ba7f0fb327624a8dde1d62943d2e92. It is for bench/phantom development. See ../docs/Design_Dossier_Draft.md for proposed requirements, unresolved design gaps and tests. No hardware deployment has been performed.

## Files and changes

- code.py: baseline firmware plus explicit BENCH_MODE, startup configuration event and audit count telemetry.
- turnlogic.py: proposed revision requiring same-side qualifying dwell with hysteresis pauses (no time credit below 30 degrees), resetting candidate evidence on sensor loss or below the 25-degree release threshold, and resuming the clock on invalid upright sensing.
- test_turnlogic.py: original eight tests plus thirteen regression/compatibility tests.
- server.py: adds an independent audited_expiries count. dashboard.html: bench banner and distinct audit/legacy labels. requirements.txt: unchanged baseline copy.

The revised rule retains both position hysteresis and turn-candidate hysteresis. Dwell pauses in the same-side 25-to-below-30-degree band, resets below 25 degrees, and accumulates only at >=30 degrees. The current angle must meet 30 degrees to complete a turn. Long band residence retains earlier qualifying time; this is not uninterrupted holding. Stillness raises technical suspicion without blocking valid turn data. Motionless phantoms can therefore count turns. Explicit BENCH_MODE=True suppresses the stillness technical warning while preserving actual sensor faults; default is False. All runs must record this setting. Team review and physical validation are needed before adopting this local version.

## Desktop checks

Use Python 3 in a terminal opened in this folder:

```text
python test_turnlogic.py
```

Expected result for this local revision: 21 tests passed. These tests need no third-party packages. Desktop tests do not establish CircuitPython library compatibility or hardware timing.

## Simulator setup

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python server.py --simulate --http 8000
```

On macOS/Linux replace `.venv\Scripts\python` with `.venv/bin/python`. Open http://127.0.0.1:8000/ in a browser. Enable browser alert sound explicitly. The Turn patient and Acknowledge buttons are simulator controls only. Stop the server with Ctrl+C.

The simulator divides interval, lead and dwell by 60. A nominal two-hour interval lasts 120 wall seconds; a nominal 15-minute lead lasts 15 wall seconds. The dashboard countdown uses the shortened wall seconds, while some labels say 15 minutes. Upright duration is counted in wall time. Simulation does not exercise physical sensing, filtering, the stillness detector, LEDs, speaker, pushbutton or actual serial acquisition. Do not use it as physical verification evidence.

Before switching to hardware, stop the service and archive the simulator-generated patch.db (and associated files if present) in a SIM-labelled run directory. Start with a separate fresh database. Do not overwrite or combine existing evidence. SQLite databases may have live -wal/-shm files; close the server and checkpoint/copy consistently before archiving.

## Board preparation

1. Confirm the exact Pico 2 W board, sensor carrier and each module's voltage/current requirements. Use the board vendor's compatible CircuitPython release; the source header mentions version 9, but compatibility has not been established here. Record the actual deployed version.
2. Install the matching CircuitPython library bundle: adafruit_lsm6ds, adafruit_register, adafruit_bus_device and neopixel.mpy in CIRCUITPY/lib. Record bundle version. Do not copy desktop packages to the board.
3. With power disconnected, wire GP8 SDA/GP9 SCL to the sensor, GP16 to NeoPixel DIN, GP18 to the amplifier input and GP20 through the button to ground. Provide a common ground. Power rails must follow the actual boards' documented ratings; the 3V3 comments in code are assumptions to check, not sufficient electrical verification.
4. Copy code.py and the reviewed turnlogic.py to CIRCUITPY. Leave Config.TIME_SCALE=1.0 for real-time tests. Do not place server.py on the Pico.
5. For a non-breathing bench phantom, explicitly set cfg.BENCH_MODE=True in code.py; use False when verifying the stillness alarm itself. This setting does not disable sensor/gravity faults. Confirm the JSON flag and dashboard banner, and archive the startup configuration event. Inspect serial output. First verify flat, known left/right and upright positions on the phantom/jig. If signs are reversed, correct the defined axis convention or ROLL_SIGN and record the change before trials.
6. Commission LED colours, speaker pulse patterns and button using T05. Check supply stability and current with all outputs active. A compatible speaker and amplifier are required; do not drive a speaker directly from a GPIO.

No CAD enclosure is supplied: measure the actual board/carrier, design a keyed fixture that prevents rotation, document clearances and cable strain relief, and provide its source and printed part when available. Do not fabricate dimensions without inspecting the components.

## Laptop connected to hardware

Discover the board's actual USB serial port in the operating system. Close any serial console using it, then run:

```text
.venv\Scripts\python server.py --port COM5 --http 8000
```

COM5 is an example, not an established port. On macOS/Linux use the actual /dev/... port. Verify that changing the jig angle changes dashboard values and inserts database samples. The board attempts reads at 20 Hz and reports about once per second. The database records only that 1-Hz summary, not the raw acquisition needed to verify sample rate.

The hardware acknowledgement is the GP20 button. The web acknowledgement endpoint is deliberately simulator-only in this version. The board has no wireless telemetry implementation despite being a W model.

## Phone notifications - registered recipients with consent

On a controlled bench network, the dashboard can also be opened from a phone at http://LAPTOP_IP:8000/. Do not expose the unauthenticated development service to the public internet.

Alerts (advisory, critical, technical) are sent only to recipients registered in the dashboard's **Alert recipients** panel, with the consent box ticked. `notify.py` stores the consent time and consent-text version, keeps withdrawn recipients for audit, and logs every send attempt in the `deliveries` table: event time, send time, latency and result. Channels: WhatsApp through CallMeBot (on the project card) or ntfy as a fallback. Message texts are fixed and contain no patient data. See ../README.md for the registration steps. Run `python test_notify.py` (10 tests, no network needed).

The old `NTFY_TOPIC` environment variable is ignored. Use **Send test** after registering, and record phone receipt time against the logged send time for T08.

## Known open issues

- Upright posture is not validated as actual bed exit; label it as a proxy.
- Shift calculations do not carry earlier critical context across boundaries and assume one upright sample per second.
- Raw values, sequence, validity, source timestamp, mode and configuration are not stored in the baseline database.
- Pico restart loses timer/latch state. Large scheduler dt gaps are not independently rejected.
- Stillness can flag quiet attached phantoms; attachment specificity is unknown.
- No physical debounce, output self-test, authenticated access or multi-patient support is present.
- Chart.js/font are external dependencies; browser sound requires user enablement.

Do not treat these as fixed merely because the local continuity tests pass. Follow T01-T09 and retain failures. Publish or deploy only after the team has reviewed the changes and the tested configuration is recorded.

## Independent audit semantics

interval_expired is emitted once per full elapsed interval since the last effective timer reset, independently of the critical latch or acknowledgement. It does not repeat critical audio or push. The lifetime counter resets at monitor restart; the next deadline resets at a qualifying turn. The service counts persisted audit events in the shift by receipt timestamp. Legacy compliance is unchanged and explicitly unvalidated. Test storage helpers without FastAPI using `python test_storage_audit.py`; this uses an in-memory SQLite database and does not test HTTP, serial or network.
