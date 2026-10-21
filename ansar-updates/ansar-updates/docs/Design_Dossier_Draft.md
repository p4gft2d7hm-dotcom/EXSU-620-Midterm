# EXSU 620 - Project 08
# Has this patient been turned?
## Repositioning monitoring patch - design dossier draft

Prepared 20 October 2026. Team: Dantha Sitompul, Carly Stroll, Ansar Tlemussov, Kyri Williams, Rachel Yoslim.

**Status: pre-build engineering draft, not a verified final submission.** The team confirmed that no physical prototype, measurements, or separate report sections are available. This dossier supplies the design narrative and a prospective verification protocol. It does not establish clinical performance. Role assignments and proposed acceptance limits require team agreement before validation data are collected.

## Evidence and revision control

The inspected baseline is `p4gft2d7hm-dotcom/EXSU-620-Midterm`, commit `bee302bf67ba7f0fb327624a8dde1d62943d2e92`, last changed 15 October 2026. The local `software/` folder includes a proposed revision of `turnlogic.py` and thirteen added regression and compatibility tests. code.py now declares and reports BENCH_MODE plus a configuration event; server.py exposes an independent audit count; dashboard.html distinguishes audit counts and bench mode. These are local revisions of the same baseline. requirements.txt remains unchanged. These local changes have not been published to GitHub or deployed to a board.

Sources reviewed:

1. EXSU620 Digital Prototyping Project Instructions, Fall 2026: overview, submission dates, D1-D9 deliverables, and team roster.
2. Shared ChatGPT project EXSU 620 Midterm: Group Project Tasks and Project Timeline, both dated 7 October. These are planning conversations, not evidence of completed work.
3. Repository source files and full visible commit history at the baseline above.

The Project 08 card is attached in the shared chat, but its download failed during preparation. The initial CR paraphrases came from the chat. A subsequent user-supplied review of the card identifies wearability as part of CR-1 and confirms the 2-hour interval in Figure 2; these corrections are incorporated here. The original PDF has still not been read directly in this workspace. Check exact wording, alarm details against it before issue. The latest user-supplied review reports that page 8, NO IDENTIFIERS requires course-participant recipients with consent and a stored consent timestamp; this requirement is now included, with implementation still open. The example report's structure was described in the chat; its performance numbers have not been adopted.

The course instructions state an in-class working session on 21 October and submission on 4 November 2026. The older chat's 21/28 October schedule was based on a preliminary assumption and is not used as the submission authority here.

### Status by deliverable

| Deliverable | Supplied in this package | Still required for completion |
|---|---|---|
| D1 | Eight proposed measurable engineering requirements and traceability | Review exact card; agree on numerical limits and threshold rationale; sign revision |
| D2 | System architecture, sensing, algorithm, alarms, data model and alternatives | Confirm assembled design; document any changes |
| D3 | Module chart and interface table | Confirm electrical ratings and actual parts |
| D4 | Four editable diagrams plus visual diagram sheet | Check wiring against actual modules and card |
| D5 | Local software copy, proposed logic fix, deployment instructions | Assemble, deploy, build enclosure/mount, test outputs and notification path; live demo |
| D6 | Prospective test methods, sample sizes, acceptance rules and sign-off roles | Assign named owners; approve protocol before execution |
| D7 | Software check results, report structure and blank data sheets | All physical measurements, labelled trials, analysis, figures and final verdicts |
| D8 | Preliminary failure analysis with mitigation status | Verify mitigations on hardware; reassess residual risk |
| D9 | Integrated draft and non-specialist memorandum | Incorporate evidence, close traceability, sign off and export final single PDF |

## D1. Engineering requirements

### Intended use and operating envelope

The prototype demonstrates orientation-based repositioning monitoring on a bench jig or torso phantom. It estimates torso roll and pitch using a rigidly mounted accelerometer, identifies four prescribed orientations, recognises sustained angular changes, and issues local and laptop alerts. It is not validated for patient use. Torso orientation alone does not establish pressure relief or true departure from a bed.

The proposed validation envelope is roll -90 to +90 degrees and pitch 0 to 80 degrees. A fixed keyed mounting orientation is assumed: Y toward the head, Z outward from the chest, and X across the chest. Commissioning must establish the actual sign of roll. Prone positions, inverted mounting, moving beds, and motion-dominated measurements are challenge conditions, not silently accepted extensions of this envelope.

### Clinical requirements to be confirmed against the card

| ID | Clinical intent, paraphrased |
|---|---|
| CR-1 | Continuously identify supine, left lateral, right lateral or upright orientation using a device the patient would be willing to wear; wording to be checked against the original card. |
| CR-2 | Warn 15 minutes before the repositioning interval expires and alert at expiry. |
| CR-3 | Do not count small or ineffective movements as effective turns. |
| CR-4 | Record turn compliance and time out of bed for each shift. |

### Requirement register

All numerical performance limits below are **proposed bench acceptance targets**, not measurements or course-mandated values. The 20 Hz acquisition, 1 Hz reporting, 30-degree turn threshold and 120-second dwell match the implementation baseline; matching existing code is not a justification of clinical suitability. Freeze an approved requirement revision before validation. Use separate development data for tuning.

| ER | Proposed requirement and acceptance criterion | CR | Verification |
|---|---|---|---|
| ER-01 Orientation accuracy | In the stated stationary envelope, report roll and pitch with absolute mean bias no greater than 3 degrees and 95th-percentile absolute error no greater than 5 degrees for each axis. Use the 105 roll and 75 pitch records defined in T01. State reference-jig uncertainty; results are inconclusive if it prevents deciding the limit. | CR-1 | T01 |
| ER-02 Acquisition and classification | Attempt acquisition at 20 Hz; measured average valid rate at least 19 Hz over each of three 60-second runs, with no unexplained valid-sample gap over 0.25 s. Report four-class orientation at least once per second. Across 60 independent settled poses, at least 95% correct classification, with at least 14/15 correct in each class; each correct output appears within 2 s of the video-marked settling time. Boundaries are tested separately rather than excluded after observing errors. | CR-1 | T02 |
| ER-03 Effective-turn discrimination | Under the proposed rule, accept a change of at least 30 degrees from the last accepted resting roll only after accumulating at least 120 qualifying seconds at or above 30 degrees on the same side of that reference, with hysteresis pauses as defined below. Invalid sensing, a change in signed direction, or falling below the 25-degree release threshold reset candidate dwell. Samples in the same-side 25-to-below-30-degree band retain the candidate but contribute no qualifying time. Stillness suspicion does not invalidate an otherwise valid angle sample. In 30 positive and 30 negative held-out trials: sensitivity at least 90%, specificity at least 95%, no duplicate events, and no acceptance in any mandatory 8-degree, interrupted-dwell or sensor-gap challenge. Report all false positives individually. | CR-3 | T03 |
| ER-04 Repositioning timer | With TIME_SCALE=1, raise advisory at 6300 s and critical at 7200 s after initialisation or an effective turn, each within 2 s of an independent elapsed-time reference. Reset only on an accepted effective event. Execute three full-duration no-turn runs plus six scripted reset cases. The 2-hour interval is confirmed by the user-supplied card cross-check (Figure 2). | CR-2, CR-3 | T04 |
| ER-05 Alarm outputs, acknowledgement and recipients | In each of ten repetitions per alarm path, local LED and sound must match the approved state table within 1 s of the internal transition. Critical audio is silenced by acknowledgement but the critical state clears only after both acknowledgement and a qualifying turn, in either order. Demonstrate three pulses for advisory and ten for critical. Laptop status appears within 2 s of the internal event. Validate repeats and technical pattern against the card. Remote recipients must be registered course participants with recorded consent timestamp; prove an unregistered or withdrawn recipient receives no message before enabling this path. This recipient requirement is not implemented by a topic name. | CR-2 | T05, T08 |
| ER-06 Technical faults and data freshness | Inject five repetitions of each defined sensor fault. A continuously invalid sensor must trigger technical indication after 5 s, within an additional 1 s output allowance. A stationary-signal challenge must trigger only after the 30-s window plus 5-s hold, within 2 s. Invalid sensor data must never accumulate turn dwell; motionlessness alone does not make angle data invalid. Dashboard stale-data indication must appear within 7 s of USB loss. Stillness is a technical suspicion, not proof of detachment. | CR-1, CR-2, CR-3 | T06 |
| ER-07 Event integrity and shift accounting | In three known event sequences spanning 07:00, 15:00 and 23:00 boundaries, persist exactly one record for each emitted event, compute turn and overdue counts exactly, and match ground-truth compliance to within rounding to the nearest percentage point. Upright-proxy duration must match known valid upright time within 2 s per interval before rounding; physical out-of-bed claims require the additional discrimination test in T07. Missing samples must not be counted as observed upright time. | CR-4 | T07 |
| ER-08 Wearability and attachment | Proposed bench design envelope for the complete worn assembly: mass <=50 g, footprint <=80 x 60 mm, thickness <=20 mm, and tool-free removal within 15 s in each of five operator trials. Across five independent mountings, survive 20 scripted turns per mounting without detachment and with mount migration <=5 mm. Record sharp edges, cable snagging and attachment damage as failures. These are proposed engineering proxies; patient willingness and comfort remain unverified by phantom tests. | CR-1 | T09 |

### Threshold decisions and rationale

The 30-degree/120-second turn rule is an engineering starting point already present in the repository. The supplied evidence does not justify it as effective clinical offloading. The team must support or revise these values using the original card, permitted course evidence and development trials, then validate the frozen rule against independently scored video. Record the evidence, rationale and revision date. Do not select thresholds on validation trials and then report those same trials as independent performance.

The revised local proposal preserves hysteresis: a candidate starts at >=30 degrees, pauses its qualifying clock in the same-side 25-to-below-30-degree band, and resets below 25 degrees, on direction reversal or sensor loss. No turn is accepted while the current sample is below 30 degrees. Thus small boundary crossings do not emit repeated partial events, while time spent in the band is never credited. This policy needs team agreement and noise testing; prolonged residence in the band retains earlier qualifying time, so it is not a claim of uninterrupted 120-second above-threshold holding. Position-classification hysteresis remains separate: enter lateral at 30 degrees, leave below/equal 20; enter upright at 60, leave below 50. These are implementation decisions, not acceptance evidence. Small changes from a lateral reference can still count if cumulative roll change reaches 30 degrees and is held; class change is not mandatory.

The current algorithm treats sustained upright orientation as a qualifying event and suspends the clock while upright. This is a prototype proxy. A raised bed backrest can produce the same pitch without actual out-of-bed activity. Until discrimination is demonstrated, label the statistic "upright time (out-of-bed proxy)" and treat CR-4's true out-of-bed requirement as open.

### Measurement uncertainty and threshold margin

Do not lower the 30-degree change threshold before calibration. Quantify the uncertainty of the angular difference, including error at both the old anchor and new pose, mounting variation and dynamic filtering. Comparing a threshold only to single-pose bias is insufficient. A useful design check is: largest intended rejected change + difference uncertainty < threshold < smallest intended accepted change - difference uncertainty. If no such gap exists, a single hard threshold cannot separate those cases reliably; revise the sensing or decision rule and validate it. Record the actual uncertainty and margin after T01 rather than claiming that nominal 30-degree positioning necessarily passes a 30-degree change rule.

### Review gate

Record approved revision, date, evidence for angle/dwell, permitted envelope, responsible reviewer and all eight acceptance limits. Team review must precede validation. Any later change requires a new revision and repetition of affected tests. No review or approval is implied by this draft.

## D2. System design

### Architecture and allocation

The Pico owns sensing, orientation, turn qualification, the repositioning clock, the bedside acknowledgement button, and local alarms. The laptop receives newline-delimited JSON over USB serial, persists samples and events in SQLite, serves a FastAPI dashboard, and optionally forwards notifications. Keeping local alarm control on the Pico avoids dependence on a browser or phone for immediate indication. The present implementation still loses elapsed state on Pico restart; restart recovery must be tested and documented.

The local package is a bench development copy. BENCH_MODE defaults to False. Setting it True disables only the stillness suspicion input to the technical alarm; sensor read failures and invalid gravity remain technical faults and reset dwell. Firmware sends bench_mode and cumulative expired_intervals in each report and queues a startup configuration event for database persistence. The dashboard shows a bench banner. Stillness metrics are still calculated. Simulator messages explicitly report bench mode, but simulation is not a physical bench test. It does not add Wi-Fi telemetry to the Pico: transport to the laptop is USB. A phone accesses the laptop dashboard on the same network or receives an optional ntfy message. The two notification paths have different failure modes and must be tested separately.

### Sensing and orientation calculation

At each loop the firmware reads acceleration in m/s^2 and applies a first-order filter to each axis: f_new = 0.85*f_previous + 0.15*a_new. At a nominal 20 Hz this smooths rapid motion, but creates delay that must be measured in T02. Roll = ROLL_SIGN*atan2(fx,fz) in degrees. Pitch = asin(fy/|f|) in degrees, clamped to a valid asin argument. The configured gravity plausibility band is 8.8-10.8 m/s^2 on the filtered vector. Dynamic acceleration can temporarily violate this band; plausible magnitude alone does not prove a valid orientation.

The gyro is available in the sensor family but is not used by the current code. Do not describe this implementation as accelerometer/gyro fusion. Static gravity supports roll/pitch but not yaw or direct measurement of pressure relief. Verify physical mounting and left/right signs before tuning thresholds.

### Position classification and effective turns

Upright classification has priority over lateral classification. Otherwise roll sign determines left/right and hysteresis suppresses boundary flicker. The initial roll is the first valid anchor. Each accepted lateral event sets a new anchor; subsequent change is a wrapped angular difference from that anchor.

In the revised local proposal, a lateral candidate accumulates only on sensor-valid samples at or above 30 degrees on one signed side of the anchor. The same-side 25-to-below-30-degree band pauses accumulation; below 25 degrees or a side reversal resets it. Sensor loss resets lateral and upright candidate accumulation. Stillness continues to raise a technical suspicion but does not gate turn qualification, so a stationary phantom can register a held turn. This prevents joining disconnected observations into a held turn. The current design does not include a maximum scheduler-gap rejection rule: a delayed loop may still contribute its elapsed dt. Add and verify such a rule if observed timing gaps exceed the approved envelope.

After 120 s of upright classification, the current monitor emits a turn event, holds the repositioning clock, and restarts it on return. This describes current software, not verified evidence of leaving bed. The local revision resumes clock progression during invalid upright sensing so that a previous upright label cannot indefinitely suppress overdue timing during sensor loss.

### Alarm state table

| State | Entry / behaviour | Local indication | Exit |
|---|---|---|---|
| Normal | Remaining time greater than 900 s; no higher-priority condition | Green, silent | Advisory threshold, critical threshold or technical overlay |
| Advisory | Remaining time <=900 s and >0 | Amber; three 880-Hz pulses (0.20 s on/0.20 s off), repeat every 30 s in code | Accepted turn resets; expiry becomes critical |
| Critical, unacknowledged | Remaining time <=0; latched | Red; ten 1200-Hz pulses (0.15 s on/0.10 s off), repeat every 5 s in code | Acknowledgement mutes; state clears only when acknowledgement AND a qualifying turn have occurred |
| Critical, acknowledged | Critical latch with ack received | Red, audio off | Qualifying turn if one has not already occurred |
| Technical overlay | Invalid sensor or stillness suspicion persists for 5 s | Cyan; 600/900-Hz chirp pattern, repeat every 20 s in code | Clears when fault timer resets; critical display has priority |
| No fresh laptop data | No message for >5 s | Dashboard grey and connection message | New message; does not itself alter Pico alarms |

Tone frequencies, repeat periods and priority are baseline implementation details to confirm against the card. The dashboard labels the old ratio as unvalidated and the upright duration as a proxy. It produces advisory/critical sound only after the user enables browser sound. It has no technical chirp implementation. The dashboard acknowledgement button works only in simulation; physical acknowledgement uses GP20.

### Audit independent of alarm state

The revised monitor emits interval_expired at each full interval of elapsed in-bed clock time since its last effective reset: 7200, 14400, 21600 nominal seconds, and so on. This emission is independent of critical/acknowledged state and does not retrigger the audible critical pattern or send a new push. An accepted turn resets the next deadline but not the cumulative audit count. Return from a counted upright episode also resets the deadline to match current timer semantics. These semantics count elapsed blocks and do not define clinical compliance.

The service persists these events with its existing event table and adds audited_expiries to the shift response. The dashboard distinguishes this count from legacy critical alarm entries. Event detail elapsed_s uses the monitor's scaled elapsed seconds (120 s per interval in a 60x demo, 7200 s at TIME_SCALE=1); record configuration to interpret it. Events are still assigned to a shift by laptop receipt time; delayed delivery around a shift boundary remains a limitation. Pico restart loses the cumulative counter and pending events. No guarantee of recoverable audit across restart or transmission loss is made.

### Data model and interfaces

Firmware messages contain roll, pitch, pos, state, acked, remaining_s, interval_s, still, ok, and an ev list of event/detail pairs. The server timestamps receipt using laptop wall time. Samples persist ts, roll, pitch, pos, state, remaining_s and still. Events persist ts, type and detail. SQLite WAL is enabled. The database is generated at runtime and is not expected as a pre-existing repository artifact.

Important omissions: raw acceleration, sample sequence numbers, source timestamps, explicit gaps, configuration revision, TIME_SCALE and validity are not persisted. Therefore the database alone cannot establish acquisition rate, reconstruct all dwell decisions, or distinguish simulation from hardware retrospectively. Before physical verification, log these fields in a separate acquisition file or extend the service schema with a versioned migration. The provided CSV forms define the evidence record to collect; they are not an automatic logger.

The endpoints are /api/status, /api/history, /api/events and /api/shift for reads; /api/ack and /api/turn are simulator-only controls. The server binds to all interfaces. This bench service has no user authentication or multi-patient identity. Use synthetic bench records and a controlled test network; do not expose it publicly or describe it as a clinical deployment.

### Notification recipients and provider rationale

According to the supplied review of card page 8, NO IDENTIFIERS, recipients must be course participants who have consented, with a recorded consent timestamp. The current server has no recipient registry, consent history, withdrawal enforcement or delivery audit. A public ntfy topic alone cannot restrict subscribers to registered recipients. Do not describe this notification path as meeting the card or use it for course-recipient verification until these controls exist. Use local-output tests meanwhile; any network integration test requires an approved registered test recipient and must preserve its consent record.

The card resource list is reported to name CallMeBot, Twilio and Meta WhatsApp, not ntfy. ntfy was inherited from the initial implementation because it offers a simple HTTP POST prototype interface. That explains the implementation choice but does not establish course acceptance or equivalent recipient controls. The group must choose an allowed provider or document and obtain any required acceptance for an alternative with appropriate access control; no provider account or recipient list was configured here. Required evidence: registered participant ID, consent timestamp (UTC), scope/channel, current active/withdrawn state, and consent check plus delivery outcome per send. Store no patient identifiers.

### Shift statistics and known limitations

Shift boundaries are 07:00, 15:00 and 23:00 in the laptop's local time. The retained legacy summary counts an on-time turn unless a preceding critical event is pending, and calculates on_time/(on_time+critical_events). This is an event-based statistic rather than a demonstrated measure of all scheduled repositioning opportunities. A critical latch can suppress additional critical events over a prolonged overdue episode; a shift beginning during a prior overdue episode loses that earlier context. These cases must be tested and the clinical definition agreed before ER-07 can pass.

Upright duration is currently upright sample count/60 minutes, assuming exactly one sample per second, including samples whose position may be stale during invalid sensing. It is not a time-integrated valid-data measurement. The simulator compresses interval/dwell by 60 but stores wall-time timestamps and upright sample counts. Never combine simulation and hardware data in the same verification database. Browser counts in demo mode are real elapsed seconds; static alert labels refer to nominal clinical time.

### Alternatives and tradeoffs

| Alternative | Decision for this prototype | Reason and consequence |
|---|---|---|
| Integrating gyro alone | Not selected | Angle would depend on initialisation and drift; gravity gives a direct static reference. Fast dynamic motion remains a limitation. |
| Accelerometer/gyro fusion | Deferred | Could improve transition handling; adds tuning and validation beyond the implemented static approach. |
| Counting every detected motion | Rejected | Small shifts could reset the timer without meeting the intended sustained-turn rule. |
| Class-change-only turns | Rejected | A meaningful angular change can occur within one lateral class; use reference angle and dwell. |
| Laptop-owned bedside alarm | Rejected | USB loss or service failure would remove local indication. |
| Wireless Pico transport | Deferred | USB is implemented and simplifies commissioning; cable management becomes a mechanical issue. |
| Bed-exit sensor in addition to IMU | Candidate future change | Needed if bed elevation cannot be distinguished from actual bed exit; not present in current hardware/code. |

## D3. Components, modules and interfaces

### Module chart

| Module | Components / software | Responsibility |
|---|---|---|
| M1 Mount and reference | Torso phantom, keyed cradle/patch, attachment, protractor jig | Repeatable orientation and independent angle reference; CAD/printed parts not yet supplied |
| M2 Sensing | LSM6DS3TR-C board, I2C wires | Acceleration measurements |
| M3 Embedded control | Raspberry Pi Pico 2 W, CircuitPython, code.py, turnlogic.py | Filter, classifier, turn/timer logic, JSON |
| M4 Bedside outputs | NeoPixel assembly, PAM8302 amplifier and compatible speaker, pushbutton | Visual/audio state and acknowledgement |
| M5 Laptop data service | USB cable, Python, pyserial, FastAPI, uvicorn, SQLite | Receive, persist, query and serve |
| M6 User/notification | Browser, Chart.js, optional ntfy topic/subscriber phone | Display, optional browser sound and remote receipt |

### Interface table

| IF | From -> to | Signal, direction and range | Baseline mapping / check |
|---|---|---|---|
| IF-01 | Mount -> sensor | Mechanical orientation, roll -90..90 degrees and pitch 0..80 proposed validation range | Fix Y headward/Z outward; measure sign and mount repeatability |
| IF-02 | Supply -> sensor/Pico | DC power and common ground | Verify exact carrier input and logic ratings on actual boards before energising |
| IF-03 | Pico <-> sensor | I2C, bidirectional SDA, clock output SCL, 3.3-V logic intended | GP8 SDA; GP9 SCL; bus frequency is not explicitly set in code |
| IF-04 | Driver -> monitor | Floating acceleration m/s^2 -> angles degrees; 20 loop attempts/s | Gravity band 8.8..10.8 m/s^2; log raw values and timestamps |
| IF-05 | Pico -> NeoPixel | One-wire digital data; 16 addressed pixels; colour values 0..255 | GP16 DIN; code assumes 3V3 power; verify actual assembly voltage/current and logic compatibility |
| IF-06 | Pico -> amplifier/speaker | PWM audio, 600..1200 Hz patterns; duty 6000/65535 in code | GP18 to amplifier A+, A- to GND; verify input requirements, speaker impedance and power |
| IF-07 | Button -> Pico | Active-low digital input with pull-up; released high/pressed low | GP20 to GND through button; debounce not implemented |
| IF-08 | Pico -> laptop | USB serial, JSON lines nominally 1 Hz; host opens 115200 | Discover actual port; do not substitute a TTL-UART pin connection |
| IF-09 | Service -> SQLite | Parameterised SQL; receipt timestamp seconds since epoch | patch.db beside server.py; WAL; separate DB for each run/mode |
| IF-10 | Browser <-> service | HTTP JSON and HTML; status polling 1 s, history polling 5 s | Port 8000 default; bind 0.0.0.0; no authentication |
| IF-11 | Service -> phone | Optional HTTPS POST to ntfy.sh/topic; receipt asynchronous | NTFY_TOPIC config; delivery not guaranteed or logged durably by baseline |
| IF-12 | Reference -> verifier | Jig angles, video timestamps and human-scored turn labels | Independent scorer; synchronise with visible/audible cue; record uncertainty |

This is an interface description of code assumptions, not a certified wiring specification. The electrical ranges of the actual carriers, LED assembly, amplifier and speaker remain to be checked. Do not use guessed voltage/current ratings to complete D3.

## D4. Diagram set

See `Diagrams.html` for four rendered diagrams and `diagrams/` for editable Mermaid sources:

1. Measurement-chain block diagram: phantom to sensor, local processing, local outputs, laptop, storage and phone.
2. Wiring diagram: exact named GP pins from code with power verification notes.
3. Alarm state chart: normal/advisory/critical latch and independent technical overlay.
4. Sequence diagram: acquisition through JSON, persistence, dashboard and optional notification.

Diagrams describe the baseline plus the explicitly labelled proposed turn-dwell revision with hysteresis pauses. They do not establish that a physical connection has been built.

## D5. Working system and deployment

See `software/README.md` for installation, software checks, simulation, board deployment and hardware commissioning. Do not replace the group's main branch without reviewing the local changes. The local proposal covers hysteresis-aware turn continuity, invalid upright timing, explicit bench configuration and independent elapsed-interval audit; the open issues in D2 are not silently fixed by documentation.

### Demonstration acceptance checklist

1. Record board, sensor carrier, firmware version, configuration and exact software revision.
2. Show four known phantom orientations, left/right sign, measured angles and database records.
3. Show an 8-degree shift without resetting the clock; show a held qualifying turn resetting once.
4. Show advisory, critical, acknowledgement-only, turn-only, and both possible orders of acknowledgement/turn.
5. Disconnect sensor and USB separately. Verify local alarm independence and stale indication.
6. Show notification receipt and log elapsed time, including any failed attempt.
7. Show upright on phantom, then raised-backrest negative challenge; describe the proxy limitation.
8. Restore normal time scale, archive evidence and replay the same dataset into the report.

## D6. Verification plan

### General procedure and independence

Use bench/phantom tests and the provided jig; no patient data. Before a session, record run ID, software revision, threshold configuration, TIME_SCALE, operator, reviewer, board/library versions, reference uncertainty, mounting photograph, supply and network conditions. Use development runs to tune; label them DEV and exclude them from final performance estimates. Freeze the final configuration and protocol before VALIDATION runs.

Align video and software time with a visible cue and a recorded event. Keep continuous time references; do not infer 20-Hz acquisition from 1-Hz telemetry. An independent scorer marks settling, movement, candidate onset, dwell completion, true turn status, sensor loss and bed-exit truth before reviewing algorithm decisions. Resolve disagreements using the predefined rule and preserve both initial labels. Never delete a failed run without documenting the reason and its replacement.

| Test | Method, apparatus and sample size | Acceptance / evidence | Execution and sign-off roles |
|---|---|---|---|
| T01 | Protractor jig; roll {-90,-60,-30,0,30,60,90} at pitch 0 and pitch {0,15,30,60,80} at roll 0. Three independent remounts; five readings >=1 s apart after 5 s settling at each point: 105 roll and 75 pitch observations. Compare the relevant axis to jig. | ER-01; calibration plot, residual plot, error summaries by angle/remount and reference uncertainty. Samples within one mounting are correlated; do not treat all readings as independent subjects. | Sensor operator; independent verification reviewer |
| T02 | Four labelled settled poses, 15 independent placements each. Add left/right/upper boundary sweeps and prone/inverted challenges. Capture raw 20-Hz timestamps in three 60-s runs; dashboard video for latency. | ER-02; confusion matrix, transition latency per trial, rate/gap table. Boundary and out-of-envelope results reported separately, not used to inflate core accuracy. | Firmware operator; systems reviewer |
| T03 | 30 qualifying turns, balanced directions; 30 negatives: ten 8-degree shifts, ten above-angle but <120-s returns, ten interrupted holds with sensor loss, below-25-degree release or side reversal, each followed by insufficient fresh qualifying time. Add separate 27-degree band-pause and noisy-boundary challenges; score them against the approved accumulated-qualifying-time rule, not uninterrupted dwell. Use independent video labels and exact 1:1 event matching. | ER-03; TP/FP/TN/FN table, all false positives, timing residuals and duplicate counts. Match acceptance to dwell completion within a proposed 2-s window; an early event is a failure. | Algorithm operator; blinded video scorer/reviewer |
| T04 | Three uninterrupted 2-hour no-turn runs at TIME_SCALE=1; additionally test critical -> accepted turn -> no acknowledgement -> another full interval and an uninterrupted six-hour audit sequence. Six reset scenarios: accepted before advisory, during advisory, after critical; rejected small shift; rejected short hold; restart. Independent stopwatch/log reference. | ER-04. Record all threshold times, reset causes and independent interval_expired events; report restart as a limitation if prior elapsed time is lost. Accelerated demo is supplementary only. | Software operator; verification reviewer |
| T05 | Video LED/audio with internal-event timestamps, ten repetitions each for normal->advisory, advisory->critical, ack->turn, turn->ack, technical->clear and critical+technical priority. Use bench injection for state transitions, plus integrated hardware check. | ER-05; pulse counts, latencies, colour, latch and mute behaviour. Browser sound requires explicit enablement. Card pattern check before approval. | UI/alarm operator; hardware reviewer |
| T06 | Run both BENCH_MODE=False and True, recording each in metadata. Confirm True suppresses only stillness, while sensor failure remains active. Five repetitions each: sensor disconnection, implausible acceleration injection, stationary detached phantom, valid quiet phantom, USB loss, reconnection. Include fault during lateral and upright dwell. | ER-06; fault onset/raise/clear times, absence of false turns, false technical alerts. A quiet attached phantom is a deliberate specificity challenge, not automatically a detached patch. | Hardware operator; verification reviewer |
| T07 | Three predetermined event timelines spanning each shift boundary, including overdue carried across boundary, repeated overdue time, data gaps and restart. Ten known upright intervals plus ten elevated-backrest intervals that are not bed exit. Use annotated wall-time intervals and ground truth. | ER-07. Publish event and scheduled-opportunity definitions separately until one is agreed. Mark true out-of-bed detection unmet if backrest cases cannot be separated. | Data operator; systems reviewer |
| T08 | Three 30-min runs at real time with sequence-numbered acquisition log, one with controlled USB outage and one with network outage. Before any notification test, require registered course-participant recipient, consent timestamp and active-consent check; these controls are currently absent, so remote verification is BLOCKED. Once implemented, test rejection of unregistered and withdrawn recipients. Ten phone notifications timed from internal event; observe local alarms with laptop disconnected. | Supplementary ER-05/ER-07 integration targets: >=99% of expected 1-Hz messages persisted, no unmarked outage >5 s, >=9/10 phone receipts within 10 s. Report failures and network conditions; these targets need the same pre-validation approval. | Integration operator; independent reviewer |
| T09 | Weigh the complete worn assembly (including worn battery/cable portion if applicable); measure three dimensions with ruler/calipers. Five independent attachments; 20 scripted manoeuvres per attachment. Photograph reference marks and measure migration. Five timed tool-free removals by a bench operator. | ER-08; wearability.csv, photos, instrument resolution, assembly inventory and failure record. Bench fit/removal are proxies; no comfort or patient acceptance claim. | Mechanical operator; independent reviewer |

### Analysis definitions

For each angle sample: residual = reported angle - reference angle, wrapped appropriately for roll. Bias = mean residual; MAE = mean absolute residual; RMSE = sqrt(mean residual squared). Report the empirical 95th percentile absolute residual, maximum error and uncertainty of the reference. Fit calibration coefficients only on DEV data. Preserve both uncorrected and corrected results.

For classification: each placement is one trial; classify using the first required post-settling report and report later stability separately. Provide a four-by-four confusion matrix and per-class recall. For effective turns: TP is one detection for one true event within the predefined completion window; FN is a missed true event; FP is a detection during a negative trial, a duplicate or an early acceptance; TN is a negative trial without any detection. Report unmatched detections separately and avoid counting many quiet seconds as independent TN trials. Sensitivity=TP/(TP+FN), specificity=TN/(TN+FP). Report denominators and a 95% binomial interval; these small samples support a bench feasibility estimate, not a clinical claim.

Measure algorithm latency from the defined true event (including required dwell), local output latency from internal transition, and notification latency from internal transition to phone receipt. Do not combine these different clocks into one unexplained latency number. For drift, leave the mounted jig at 0 degrees for a proposed 30 minutes before and after the test session, recording each minute; report change from initial bias and temperature if available. This drift subtest is supplementary to T01 and is required in D7; proposed limit is <=3 degrees change, subject to the same review gate as D1.

### Evidence files

Use one directory per run. Retain metadata, immutable raw acquisition CSV, original serial JSON lines, database copy with WAL checkpoint, video, independently scored labels, analysis output, figures and a signed test record. Record missing fields explicitly. The provided empty CSV files are templates, not collected data. No fabricated rows are included.

## D7. Verification report - available evidence and pending results

### Completed software checks

On 20 October 2026, the eight existing monitor tests were run on desktop Python and passed for the inspected baseline. The local proposal passes those eight tests and thirteen additional tests, covering: hysteresis-band pause without credit, sensor-gap continuity, opposite-side dwell reset, stationary-phantom compatibility, invalid-upright timing, noisy threshold compatibility, release-threshold reset inability to start or complete a turn in the hysteresis band, bench-mode phantom operation, sensor-fault protection in bench mode, repeated audit while critical is latched, one audit event per elapsed block, and audit deadline reset after an early turn. A separate in-memory SQLite helper check verifies that two audit expiries and one critical entry are persisted and counted separately without additional pushes. This helper check excludes web, serial and network setup. See `verification/software_test_results.txt` for recorded output and `software/test_turnlogic.py` for executable scenarios. These are deterministic software checks; they contain no hardware accuracy, calibrated timing or human-subject evidence.

### Verification summary

| ER / check | Current verdict | Evidence / reason |
|---|---|---|
| ER-01 | NOT TESTED | No jig measurements or calibration/residual data |
| ER-02 | NOT TESTED | No hardware rate, classification or latency observations |
| ER-03 | NOT VERIFIED | Deterministic logic scenarios pass; held-out video trials and threshold justification absent |
| ER-04 | NOT VERIFIED | Scripted timing checks pass; three independent real-time runs absent |
| ER-05 | NOT VERIFIED | Monitor latch scenarios pass; physical outputs untested; registered-recipient consent and timestamp enforcement absent |
| ER-06 | NOT VERIFIED | Several injected monitor behaviours tested; physical fault detection/specificity untested |
| ER-07 | OPEN DESIGN GAP | Independent elapsed-interval audit tested in software; compliance definition, true bed exit, receipt-time shift allocation and duration integration remain open |
| ER-08 | NOT TESTED | No complete wearable assembly, mass/dimensions, attachment or removal measurements |

### Required final results narrative

For each T01-T09, add: frozen revision and configuration, date, apparatus and uncertainty, operator/reviewer, actual sample size and exclusions, method departures, quantitative results, figures/tables, pass/fail against the preapproved ER, failure cause and corrective action. Separate retest results from the original failure. Retain failures in the evidence history.

Required figures: (1) reference versus measured roll and pitch with identity line; (2) roll/pitch residuals versus reference; (3) stationary drift versus elapsed time; (4) labelled example timeline showing true turns, rejected shifts, alarms and faults; (5) classification confusion matrix; (6) local/dashboard/phone latency distributions. Do not generate performance curves from the simulator and label them physical results.

## D8. Failure modes and mitigation

This is a preliminary bench FMEA. Score severity (S), occurrence (O) and difficulty of detection (D) from 1 (low/easily detected) to 5 (high/hard to detect); RPN=S*O*D prioritises work, not clinical acceptability. O and D are engineering estimates before testing. Residual risk cannot be marked accepted until mitigation evidence and a reviewer are recorded.

| FM | Failure / effect | S/O/D; RPN | Mitigation and implementation status | Verification / residual status |
|---|---|---|---|---|
| FM-01 | Inverted or slipping mount swaps side or fakes a turn | 4/3/3;36 | Keyed cradle and mounting check proposed; roll sign configurable; no supplied CAD or slip detector | T01/T02 remount and slip challenges; OPEN |
| FM-02 | Small movement/short hold resets timer falsely | 5/3/3;45 | Angle+dwell present; proposed hysteresis pause without time credit and direction reset added locally | Original + added software tests pass; T03 physical validation pending |
| FM-03 | Sensor gap bridges two partial holds | 5/3/4;60 | Candidate reset on invalid sample added locally; scheduler-gap rejection still absent | Added test passes; T06 and sampling-gap test pending |
| FM-04 | Sensor unplugged or invalid output masks due turn | 5/2/2;20 | Five-second technical alarm and retry present; local invalid-upright clock resumption added | T06 physical alarm/recovery pending |
| FM-05 | Quiet attached patch falsely flagged detached | 3/4/3;36 | Stillness heuristic remains unvalidated; explicit bench mode suppresses only this suspicion on a phantom, preserves sensor faults and is labelled in telemetry/dashboard | Bench-mode software checks pass; physical quiet-attached vs detached T06 OPEN |
| FM-06 | Raised backrest treated as bed exit; timer suppressed | 5/4/4;80 | Proxy limitation documented; true bed-exit sensing or validated additional cue not implemented | T07; true out-of-bed claim OPEN |
| FM-07 | Pico restart loses interval and alarm state | 5/2/4;40 | No persistence/recovery implemented; commissioning/reset visible procedure proposed | Restart T04/T07; OPEN |
| FM-08 | USB/service/network loss removes remote alert | 4/3/2;24 | Pico local alarms independent; dashboard stale indicator and serial reconnect present; phone retry/audit limited | T06/T08; OPEN |
| FM-09 | Button bounce or failed speaker prevents intended interaction | 4/2/3;24 | Edge detection present; debounce/output self-test not implemented; pre-demo manual checks proposed | T05 physical test; OPEN |
| FM-10 | LED/amplifier power mismatch causes reset/damage | 4/2/3;24 | Verify exact ratings, current budget and common ground before wiring; code comments alone insufficient | Hardware inspection and supply test; OPEN |
| FM-11 | Missing/duplicate messages bias duration/compliance | 4/3/4;48 | SQLite persistence present; sequence/validity/mode fields and time integration absent | T07/T08; OPEN |
| FM-12 | Critical latch suppresses repeated expiry; shift boundary mislabels compliance | 4/3/4;48 | Independent interval_expired audit now counts elapsed blocks despite latch; legacy compliance and receipt-time shift carryover remain unresolved | Monitor and SQLite helper checks pass; T07 physical/end-to-end and compliance definition OPEN |
| FM-13 | Browser dependency unavailable or sound disabled | 3/3/2;18 | Local Pico outputs remain; Chart.js/font externally hosted; browser audio opt-in | T08 offline/browser checks; OPEN |
| FM-14 | Simulation records mistaken for validation | 4/3/4;48 | Separate folders/databases and run metadata required; mode not stored by baseline | Evidence audit before report; OPEN |

Mitigations described as proposed or procedural have not been implemented merely by adding them to this table. Add a post-test residual S/O/D, evidence ID and named reviewer for each row. Prioritise false-turn errors, out-of-bed ambiguity and loss of timer state before adding cosmetic features.

## D9. Traceability and technical memorandum

The editable `verification/traceability.csv` maps CR -> ER -> implementation -> test -> evidence -> verdict. Every final pass must point to an actual run and figure. A test result cannot close a requirement with a different revision or unapproved criterion. The final dossier must include signed reviews, the tested revision, final electrical/mounting drawings, all evidence summaries, limitations and the following updated non-specialist memorandum.

### Technical memorandum for a non-specialist reader

**To:** EXSU 620 project reviewers  
**From:** Project 08 team  
**Subject:** What the repositioning patch can demonstrate and what remains unverified

The project aims to show whether a torso-mounted sensor can recognise a sustained change in orientation and remind a caregiver when the next turn is due. A small computer reads the sensor, checks whether a movement meets an agreed angle-and-duration rule, and controls a bedside light and sound. A laptop records events and presents a dashboard. The system distinguishes the patient's current position from a qualifying turn: a brief movement should not restart the repositioning clock.

The software foundation is available and scripted monitor tests pass. A revised local proposal resets turn evidence on sensor failure or a return below the hysteresis release angle. Boundary-band samples pause qualifying time, and stationary-phantom samples remain eligible when the sensor is valid. These checks show that selected logical cases behave as intended in desktop Python. They do not establish how accurately a physical patch measures orientation or whether the chosen rule represents adequate pressure relief.

The next stage is to build the phantom prototype and compare its outputs against a protractor jig and independently scored video. The team will measure angle error, classification, false and missed turns, alarm timing, fault response and record completeness using criteria agreed before validation. The report will retain failures and identify their causes. The complete worn assembly must also be measured for mass, dimensions, attachment stability and removal time; these bench measurements do not establish comfort or willingness to wear it.

Two limitations are particularly important. Upright torso orientation can result from raising a bed backrest, so it cannot yet establish that a person has left bed. Restarting the embedded computer also loses the previous interval state. These limitations must be resolved or explicitly reported as unmet requirements. No clinical-use or performance claim is made at this stage.

### Final assembly and submission checklist

- Verify exact card and permitted threshold evidence; approve D1/D6 revision.
- Assign named execution and independent review owners; record actual contributions.
- Build and photograph the mounting and wiring; include CAD/printed-part files where required.
- Run software checks, commissioning and T01-T09; preserve raw evidence and failures.
- Fix or report open design gaps; retest changed behaviour with a new revision.
- Populate D7, FMEA residual risk and traceability with real evidence IDs.
- Review all diagrams against the tested build and replace draft labels appropriately.
- Assemble the required 3-4-page D1, 4-6-page D2 and 6-10-page D7 with supporting tables/figures; this working draft is not yet paginated to those targets.
- Export a single labelled PDF with project number/title and all member names; check readability, figure numbering and cross-references.
- Submit by the confirmed course deadline; preserve an editable source and evidence archive.
