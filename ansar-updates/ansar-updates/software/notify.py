"""
notify.py  -  registered message recipients, consent records and the delivery log.

Project card, page 8 (NO IDENTIFIERS): no patient identifiable information enters the
database or any message, and message recipients are course participants who have
opted in, with the consent timestamp stored. This module enforces that:

  * Messages are sent only to recipients with a stored consent timestamp and no
    withdrawal timestamp.
  * Message text is fixed per event type and never contains patient data.
  * Every attempt is written to the deliveries table: who, which event, when the
    event happened, when the send finished, whether it worked, and the latency.

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
        sent_ts REAL NOT NULL,           -- when the send attempt finished
        latency_s REAL NOT NULL,         -- sent_ts - event_ts (laptop side only)
        ok INTEGER NOT NULL,
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
    """Real network send. Returns (ok, detail)."""
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


def dispatch(con, event, event_ts, sender=http_send, clock=time.time):
    """Send one event to every consenting recipient and log each attempt.
    Returns the number of successful deliveries."""
    if event not in TEXTS:
        return 0
    text = TEXTS[event]
    sent = 0
    for rec in active(con):
        ok, detail = sender(rec, text)
        done = clock()
        con.execute("INSERT INTO deliveries(recipient_id,event,event_ts,sent_ts,latency_s,ok,detail)"
                    " VALUES(?,?,?,?,?,?,?)",
                    (rec["id"], event, event_ts, done, round(done - event_ts, 3),
                     1 if ok else 0, detail[:300]))
        sent += 1 if ok else 0
    return sent


def deliveries(con, limit=100):
    rows = con.execute("SELECT d.id,d.event,d.event_ts,d.sent_ts,d.latency_s,d.ok,d.detail,"
                       "r.name,r.channel FROM deliveries d JOIN recipients r ON r.id=d.recipient_id "
                       "ORDER BY d.id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
