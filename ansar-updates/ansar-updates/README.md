# Updates from Ansar — 20 October 2026

This folder adds proposed fixes and draft documentation. **Nothing in the main project folder was changed.** The original code (Carly's upload, commit `bee302b`) stays where it is, so we can compare the two versions and decide together what to adopt.

Everything here was checked on a laptop only. No hardware testing has been done yet.

## What is in this folder

| Folder | Contents |
|---|---|
| `software/` | Revised `turnlogic.py`, `code.py`, `server.py`, `dashboard.html`, plus tests (21 logic tests and an SQLite audit test, all passing) |
| `docs/` | Draft design dossier covering D1–D9, and the four D4 diagrams (block, wiring, alarm state chart, sequence) as editable Mermaid files and SVG |
| `verification/` | Blank data-collection forms for the bench tests, the traceability matrix (CR → ER → test), and the software test log |

## Fixes to the code

We reviewed the original code and found several problems. These versions fix them:

1. **Missed intervals were lost while the critical alarm was latched.** If the critical alarm stayed on (turned but not acknowledged) and another two hours passed without a turn, the second missed interval was never recorded. Each overdue interval is now logged as a separate `interval_expired` event, independent of the alarm state. This matters for CR-4 (audit).
2. **Time in the 25–30° band counted towards a turn.** A patient could touch 35° for one second, lie at 27° for 200 seconds, return to 35° briefly, and get credited with a turn. Hold time now accumulates only at ≥30°. It pauses in the 25–30° band and resets below 25°.
3. **A sensor dropout could stitch two partial holds into one turn.** Hold time now resets whenever sensor data is lost.
4. **On a non-breathing bench phantom the technical alarm would fire about 35 s after start.** We added an explicit `BENCH_MODE` setting that suppresses only the "motionless" warning. Real sensor faults still raise the technical alarm. The setting is logged in every data line so each test run shows which mode it used.
5. **Turn direction:** a reversal to the other side now resets a candidate turn instead of carrying over hold time.

The 30° angle and 120 s dwell are **unchanged**. They still need evidence from the literature and our calibration.

## Draft documents

- **D1:** eight engineering requirements (ER-01 to ER-08), each with a numeric pass/fail criterion, sample size and link to CR-1–CR-4. These are proposals for the group to agree on, not final values.
- **D2, D3, D6, D8:** draft text and tables. The D9 traceability matrix is in `verification/traceability.csv`, with every row currently marked NOT TESTED.
- No measurement results have been invented. The CSV files are empty forms.

## Decisions needed from the group

1. **Compliance definition.** The shift summary still uses the old formula, which can be inflated by frequent turns. We need to agree on what counts as an on-time interval before changing it.
2. **Out of bed vs upright.** A bed head raised above 60° currently counts as "out of bed". We need a better signal or must state this limitation clearly in the report.
3. **Registered message recipients.** The project card (page 8) requires recipients to be opted-in course participants with a stored consent timestamp. This is not implemented yet. ntfy.sh is not on the card's resource list, so we either justify it in the design rationale or switch to one of the listed services.
4. **Before bench runs, set `cfg.BENCH_MODE = True` in `software/code.py`.** The default is False.

## How to run

```text
cd ansar-updates/software
python test_turnlogic.py
python server.py --simulate --http 8000
```

Then open http://127.0.0.1:8000/. See `software/README.md` for board setup.
