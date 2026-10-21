"""
notify.py  -  registered message recipients, consent records and the delivery log.

Project card, page 8 (NO IDENTIFIERS): no patient identifiable information enters the
database or any message, and message recipients are course participants who have
opted in, with the consent timestamp stored. This module enforces that:

  * Messages are sent only to recipients with a stored consent timestamp and no
    withdrawal timestamp.
  * Message text is fixed per event type and never contains patient data.
  * Every attempt is written to the deliveries table: who, which event, when the
    event happened, when the provider answered, whether the provider ACCEPTED the
    request, and that latency. Provider acceptance is not phone receipt: the time a
    message actually appears on the phone is measured by hand in T08.
  * Consent is re-checked immediately before each send, so a withdrawal recorded
    while a dispatch is running stops every send that has not started yet.
  * No database transaction is held open during a network call, so a slow provider
    cannot block the telemetry writes from the patch.

Channels
  callmebot : WhatsApp through CallMeBot (listed on the project card). Each person
              activates their own number and receives their own API key. The free
              service is for personal use, which fits: each participant registers
              their own phone.
  ntfy      : push through ntfy.sh (NOT on the card's resource list; kept as a fallback
              because CallMeBot activation is not always available). Each recipient
              uses their own hard-to-guess topic. Its use must be justified in the
              design rationale.

Pure standard library, so it can be tested without FastAPI.
"""
import time
import urllib.parse
import urllib.request

CONSENT_VERSION = "v1"
CONSENT_TEXT = (
    "I am a participant in EXSU 620 Project 08. I agree to receive bench-test alert "
    "messages from the repositioning patch prototype on the channel I registered. "
    "No patient information is sent. I can withdraw at any time."
)

CHANNELS = ("callmebot", "ntfy")
ALERT_EVENTS = ("advisory", "critical", "technical")

# Fixed texts. Nothing here may ever include patient data.
TEXTS = {
    "advisory": "[EXSU620 bench patch] Turn due in 15 minutes.",
    "critical": "[EXSU620 bench patch] Turn overdue. No effective turn recorded.",
    "technical": "[EXSU620 bench patch] Technical alarm: check the patch.",
    "test": "[EXSU620 bench patch] Test message. You are registered for alerts.",
}


class RegistrationError(ValueError):
    pass


# ------------------------------------------------------------------- schema
def init(con):
    # A database made by the first draft of this module has a deliveries table with
    # different columns. Keep it under another name rather than deleting evidence.
    cols = [r[1] for r in con.execute("PRAGMA table_info(deliveries)").fetchall()]
    if cols and "accepted" not in cols:
        con.execute("ALTER TABLE deliveries RENAME TO deliveries_old_draft")
        con.execute("DROP INDEX IF EXISTS i_deliv")
    con.execute("""CREATE TABLE IF NOT EXISTS recipients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,              -- participant name or initials, never a patient
        channel TEXT NOT NULL,           -- callmebot | ntfy
        address TEXT NOT NULL,           -- phone with country code, or ntfy topic
        apikey TEXT,                     -- CallMeBot key; not returned by the API
        consent_ts REAL NOT NULL,        -- when consent was given (unix time)
        consent_version TEXT NOT NULL,
        withdrawn_ts REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS deliveries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER NOT NULL,
        event TEXT NOT NULL,
        event_ts REAL NOT NULL,          -- when the patch event reached the laptop
        answered_ts REAL NOT NULL,       -- when the provider answered (or the attempt failed)
        accept_latency_s REAL NOT NULL,  -- answered_ts - event_ts. NOT phone receipt time
        accepted INTEGER NOT NULL,       -- 1 = provider accepted the request
        detail TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS i_deliv ON deliveries(event_ts)")


# ------------------------------------------------------------- registration
def _clean_address(channel, address):
    address = (address or "").strip()
    if channel == "callmebot":
        digits = address.replace(" ", "").replace("-", "")
        if not (digits.startswith("+") and digits[1:].isdigit() and 8 <= len(digits) <= 16):
            raise RegistrationError("phone must include the country code, e.g. +15145550123")
        return digits
    if channel == "ntfy":
        ok = all(ch.isalnum() or ch in "-_" for ch in address)
        if not ok or len(address) < 12:
            raise RegistrationError("ntfy topic must be at least 12 letters, digits, - or _")
        return address
    raise RegistrationError("channel must be one of: " + ", ".join(CHANNELS))


def register(con, name, channel, address, consent, apikey=None, now=None):
    """Add a recipient. Refuses unless consent is explicitly True."""
    if consent is not True:
        raise RegistrationError("consent is required before anyone can receive messages")
    name = (name or "").strip()
    if not name or len(name) > 60:
        raise RegistrationError("give a participant name or initials (up to 60 characters)")
    if channel not in CHANNELS:
        raise RegistrationError("channel must be one of: " + ", ".join(CHANNELS))
    address = _clean_address(channel, address)
    if channel == "callmebot" and not (apikey or "").strip():
        raise RegistrationError("CallMeBot needs the API key the bot sent you")
    now = time.time() if now is None else now
    cur = con.execute(
        "INSERT INTO recipients(name,channel,address,apikey,consent_ts,consent_version)"
        " VALUES(?,?,?,?,?,?)",
        (name, channel, address, (apikey or "").strip() or None, now, CONSENT_VERSION))
    return cur.lastrowid


def withdraw(con, recipient_id, now=None):
    """Withdraw consent. The row is kept for audit, but nothing more is sent."""
    now = time.time() if now is None else now
    cur = con.execute("UPDATE recipients SET withdrawn_ts=? WHERE id=? AND withdrawn_ts IS NULL",
                      (now, recipient_id))
    return cur.rowcount == 1


def active(con):
    return con.execute("SELECT * FROM recipients WHERE withdrawn_ts IS NULL "
                       "AND consent_ts IS NOT NULL ORDER BY id").fetchall()


def _mask(channel, address):
    if channel == "callmebot":
        return address[:2] + "•" * max(0, len(address) - 6) + address[-4:]
    return address[:4] + "•" * max(0, len(address) - 4)


def listing(con):
    """Public view for the dashboard: addresses masked, API keys never returned."""
    rows = con.execute("SELECT id,name,channel,address,consent_ts,consent_version,withdrawn_ts "
                       "FROM recipients ORDER BY id").fetchall()
    return [{"id": r["id"], "name": r["name"], "channel": r["channel"],
             "address": _mask(r["channel"], r["address"]),
             "consent_ts": r["consent_ts"], "consent_version": r["consent_version"],
             "withdrawn_ts": r["withdrawn_ts"]} for r in rows]


# ------------------------------------------------------------------ sending
def http_send(recipient, text, timeout=10):
    """Real network send. Returns (accepted, detail).
    accepted means the provider took the request; it does not prove the phone got it.
    For CallMeBot, which can answer HTTP 200 with an error text, a body containing
    'error' is treated as not accepted. That is a heuristic, not a documented contract."""
    if recipient["channel"] == "callmebot":
        q = urllib.parse.urlencode({"phone": recipient["address"], "text": text,
                                    "apikey": recipient["apikey"] or ""})
        req = urllib.request.Request("https://api.callmebot.com/whatsapp.php?" + q)
    else:
        req = urllib.request.Request("https://ntfy.sh/" + recipient["address"],
                                     data=text.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(300).decode("utf-8", "ignore")
            status = r.status
        # CallMeBot can answer 200 with an error message in the body.
        failed = recipient["channel"] == "callmebot" and "error" in body.lower()
        return (200 <= status < 300 and not failed), "HTTP %d %s" % (status, body[:120].strip())
    except Exception as e:  # network down, bad key, timeout
        return False, "%s: %s" % (type(e).__name__, e)


def is_active(con, recipient_id):
    return con.execute("SELECT * FROM recipients WHERE id=? AND withdrawn_ts IS NULL",
                       (recipient_id,)).fetchone()


def log_attempt(con, recipient_id, event, event_ts, answered_ts, accepted, detail):
    """Write one attempt and commit at once, so no write lock outlives this call."""
    con.execute("INSERT INTO deliveries(recipient_id,event,event_ts,answered_ts,"
                "accept_latency_s,accepted,detail) VALUES(?,?,?,?,?,?,?)",
                (recipient_id, event, event_ts, answered_ts,
                 round(answered_ts - event_ts, 3), 1 if accepted else 0, detail[:300]))
    con.commit()


def dispatch(con, event, event_ts, sender=http_send, clock=time.time):
    """Send one event to every consenting recipient and log each attempt.
    Returns the number of attempts the provider accepted."""
    if event not in TEXTS:
        return 0
    text = TEXTS[event]
    con.commit()                       # never start a network call inside a transaction
    accepted = 0
    for rid in [r["id"] for r in active(con)]:
        rec = is_active(con, rid)      # consent re-checked right before this send
        if rec is None:
            continue
        ok, detail = sender(rec, text)
        log_attempt(con, rid, event, event_ts, clock(), ok, detail)
        accepted += 1 if ok else 0
    return accepted


def deliveries(con, limit=100):
    rows = con.execute("SELECT d.id,d.event,d.event_ts,d.answered_ts,d.accept_latency_s,"
                       "d.accepted,d.detail,"
                       "r.name,r.channel FROM deliveries d JOIN recipients r ON r.id=d.recipient_id "
                       "ORDER BY d.id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
