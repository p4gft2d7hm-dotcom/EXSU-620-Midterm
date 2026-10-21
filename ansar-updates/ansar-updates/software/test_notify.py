"""
test_notify.py  -  recipient registry, consent and delivery log (no network).
Run with:  python test_notify.py
"""
import sqlite3

import notify


def fresh():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    notify.init(con)
    return con


def fake_sender(log, ok=True):
    def send(rec, text):
        log.append((rec["name"], text))
        return ok, "fake"
    return send


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except notify.RegistrationError:
        return True
    return False


def test_registration_requires_consent():
    con = fresh()
    assert raises(notify.register, con, "AT", "ntfy", "exsu620-at-x7k2q9", consent=False)
    assert raises(notify.register, con, "AT", "ntfy", "exsu620-at-x7k2q9", consent="yes")
    assert con.execute("SELECT COUNT(*) FROM recipients").fetchone()[0] == 0


def test_consent_timestamp_is_stored():
    con = fresh()
    rid = notify.register(con, "AT", "ntfy", "exsu620-at-x7k2q9", consent=True, now=1000.0)
    row = con.execute("SELECT * FROM recipients WHERE id=?", (rid,)).fetchone()
    assert row["consent_ts"] == 1000.0 and row["consent_version"] == notify.CONSENT_VERSION


def test_address_and_key_validation():
    con = fresh()
    assert raises(notify.register, con, "AT", "callmebot", "5145550123", True, apikey="1")
    assert raises(notify.register, con, "AT", "callmebot", "+15145550123", True)  # no key
    assert raises(notify.register, con, "AT", "ntfy", "short", True)
    assert raises(notify.register, con, "AT", "sms", "+15145550123", True)
    assert raises(notify.register, con, "", "ntfy", "exsu620-at-x7k2q9", True)
    notify.register(con, "AT", "callmebot", "+1 514-555-0123", True, apikey="123456")
    assert con.execute("SELECT address FROM recipients").fetchone()[0] == "+15145550123"


def test_only_consenting_recipients_receive():
    con = fresh()
    a = notify.register(con, "AT", "ntfy", "exsu620-at-x7k2q9", True)
    notify.register(con, "CS", "ntfy", "exsu620-cs-p3m8w1", True)
    notify.withdraw(con, a)
    sent = []
    n = notify.dispatch(con, "critical", 100.0, sender=fake_sender(sent), clock=lambda: 101.5)
    assert n == 1 and [s[0] for s in sent] == ["CS"], sent


def test_no_recipients_means_no_messages():
    con = fresh()
    sent = []
    assert notify.dispatch(con, "critical", 0.0, sender=fake_sender(sent)) == 0 and sent == []


def test_every_attempt_is_logged_with_latency():
    con = fresh()
    notify.register(con, "CS", "ntfy", "exsu620-cs-p3m8w1", True)
    notify.dispatch(con, "advisory", 100.0, sender=fake_sender([], ok=False), clock=lambda: 102.25)
    d = notify.deliveries(con)[0]
    assert d["event"] == "advisory" and d["ok"] == 0 and d["latency_s"] == 2.25, d


def test_messages_carry_no_patient_data():
    for text in notify.TEXTS.values():
        assert text.startswith("[EXSU620 bench patch]")
    con = fresh()
    notify.register(con, "CS", "ntfy", "exsu620-cs-p3m8w1", True)
    sent = []
    notify.dispatch(con, "critical", 0.0, sender=fake_sender(sent))
    assert sent[0][1] == notify.TEXTS["critical"]


def test_listing_masks_address_and_hides_key():
    con = fresh()
    notify.register(con, "AT", "callmebot", "+15145550123", True, apikey="987654")
    item = notify.listing(con)[0]
    assert "apikey" not in item and "987654" not in str(item)
    assert item["address"].endswith("0123") and "5145550" not in item["address"]


def test_withdraw_is_kept_for_audit():
    con = fresh()
    rid = notify.register(con, "AT", "ntfy", "exsu620-at-x7k2q9", True, now=10.0)
    assert notify.withdraw(con, rid, now=20.0)
    assert not notify.withdraw(con, rid, now=30.0)          # already withdrawn
    row = notify.listing(con)[0]
    assert row["consent_ts"] == 10.0 and row["withdrawn_ts"] == 20.0


def test_unknown_event_is_not_sent():
    con = fresh()
    notify.register(con, "CS", "ntfy", "exsu620-cs-p3m8w1", True)
    sent = []
    assert notify.dispatch(con, "interval_expired", 0.0, sender=fake_sender(sent)) == 0
    assert sent == []


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("pass ", t.__name__)
    print("%d tests passed" % len(tests))
