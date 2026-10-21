# Updates from Ansar — 20 October 2026

This folder adds proposed fixes and draft documentation. **Nothing in the main project folder was changed.** The original code (Carly's upload, commit `bee302b`) stays where it is, so we can compare the two versions and decide together what to adopt.

Everything here was checked on a laptop only. No hardware testing has been done yet.

## What is in this folder

| Folder | Contents |
|---|---|
| `software/` | Revised `turnlogic.py`, `code.py`, `server.py`, `dashboard.html`, new `notify.py`, plus tests (21 logic tests, 13 notification tests and an SQLite audit test, all passing) |
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

## Registered alert recipients (added 20 Oct, evening)

The project card (page 8, NO IDENTIFIERS) requires message recipients to be course participants who opted in, with the consent timestamp stored. Previously the server pushed to one public ntfy topic with no list and no consent. Now:

- `software/notify.py` keeps a `recipients` table (name or initials, channel, address, consent time, consent text version, withdrawal time) and a `deliveries` table (event, recipient, event time, provider answer time, whether the provider accepted the request, error).
- Messages go **only** to recipients with consent and no withdrawal. Registration without the consent box ticked is refused. Consent is re-checked right before each message, so a withdrawal takes effect even in the middle of sending an alert.
- **Only the laptop running the service can add, withdraw or test recipients.** Phones on the Wi-Fi can view the dashboard but get "403 refused" for these actions. This is our controlled procedure: the operator registers each participant in person, after they agree. The code cannot prove someone is a course participant; the in-person procedure does.
- Message texts are fixed per alarm type and contain no patient data.
- Two channels: **WhatsApp via CallMeBot** and **ntfy** (fallback).
- Withdrawn recipients stay in the table for audit, but nothing more is sent to them. API keys are never returned by the API, and phone numbers are masked on the dashboard.
- The log records when the **provider accepted** each message. That is not proof the phone received it. Phone receipt time is measured by hand in T08 (ER-05) against the logged time.
- Network calls never run inside an open database transaction, so a slow messaging service cannot block the patch data from being saved.
- Dashboard: new **Alert recipients** panel (register, Send test, Withdraw) and a **Message delivery log**.
- `software/test_notify.py`: 13 tests (consent required, only active recipients receive, withdrawal before and during sending, logging, masking, no patient data, database not locked by a slow provider, old-draft table kept).

**How each person registers (WhatsApp):**
1. Follow the activation steps at https://www.callmebot.com/blog/free-api-whatsapp-messages/. You send the bot a WhatsApp message and it replies with your personal API key.
2. At the laptop running the service, with the operator: enter your name, phone with country code (+1...) and the key, read the consent text, tick the box, then click **Register**.
3. Click **Send test** and confirm that the message arrived on your phone.

**ntfy instead:** install the ntfy app, subscribe to a topic only you know (at least 12 characters, e.g. `exsu620-yourname-x7k2q`), and register that topic on the laptop. Note: ntfy cannot stop someone else who guesses the topic from subscribing, and withdrawing here does not remove your subscription in the app. Unsubscribe in the app as well.

The old `NTFY_TOPIC` environment variable is no longer used.

Limitations for D8: there is no user login, so access control is "only the laptop can manage recipients". Anyone using that laptop can manage them. For CallMeBot, treating a reply that contains "error" as not accepted is a heuristic, not a documented response format.

## Draft documents

- **D1:** eight engineering requirements (ER-01 to ER-08), each with a numeric pass/fail criterion, sample size and link to CR-1–CR-4. These are proposals for the group to agree on, not final values.
- **D2, D3, D6, D8:** draft text and tables. The D9 traceability matrix is in `verification/traceability.csv`, with every row currently marked NOT TESTED.
- No measurement results have been invented. The CSV files are empty forms.

## Evidence for the thresholds

`docs/Literature_D2_thresholds.md` collects the sources for D2. In short: **30°** matches the international guideline's preferred tilt. **2 h** is the card's standard. **We found no source for the 120 s dwell.** The large wearable-sensor RCT (Pickham et al.) used at least **15 min** of tissue decompression as its protocol definition. That is one study's protocol, not a universal threshold, but it is the closest published reference. The code keeps 30° / 120 s until the group decides.

## Decisions needed from the group

1. **Compliance definition.** The shift summary still uses the old formula, which can be inflated by frequent turns. We need to agree on what counts as an on-time interval before changing it.
2. **Out of bed vs upright.** A bed head raised above 60° currently counts as "out of bed". We need a better signal or must state this limitation clearly in the report.
3. **Notification channel.** WhatsApp through CallMeBot (on the card) is the default. CallMeBot currently warns that new activations may be delayed, so ntfy is kept as a fallback. If we end up using ntfy, the design rationale needs a line explaining why, because it is not on the card's resource list.
4. **Dwell time: keep 120 s (state it as an engineering rule) or move to 15 min.** See the literature note. Any change to when the advisory clears must still match Figure 3 of the card.
5. **Before bench runs, set `cfg.BENCH_MODE = True` in `software/code.py`.** The default is False.

## How to run

```text
cd software
python test_turnlogic.py
python test_notify.py
python server.py --simulate --http 8000
```

Run these from inside this folder (the one containing this README). Then open http://127.0.0.1:8000/. See `software/README.md` for board setup.

`docs/Design_Dossier_Draft.md` is the editable source; `docs/Design_Dossier_Draft.html` is rendered from it for reading in a browser.
