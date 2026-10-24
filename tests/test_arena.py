import random

import numpy as np
from fastapi.testclient import TestClient

from arena.evaluate import metrics, run
from arena.guardian import KeywordGuardian, TextGuardian, threshold_for_fpr
from arena.scenarios import HELD_OUT_TYPES, SEEN_TYPES, TACTICS, make_dataset


def test_deterministic():
    assert make_dataset(5, 50) == make_dataset(5, 50)


def test_labels_and_types():
    d = make_dataset(1, 400)
    assert 0.25 < np.mean([e["label"] for e in d]) < 0.55
    assert {e["kind"] for e in d if e["label"]} <= set(SEEN_TYPES)
    h = make_dataset(1, 200, scam_types=HELD_OUT_TYPES, variant="C")
    assert {e["kind"] for e in h if e["label"]} <= set(HELD_OUT_TYPES)


def test_wording_sets_do_not_overlap():
    for t, v in TACTICS.items():
        assert not set(v["A"]) & set(v["B"]) and not set(v["A"]) & set(v["C"]) and not set(v["B"]) & set(v["C"])


def test_no_real_identifiers_in_text():
    import re
    for e in make_dataset(2, 300):
        assert not re.search(r"\d{6,}|@|https?://", e["text"])


def test_keyword_rules_break_when_wording_changes():
    tr, b = make_dataset(1, 800, variant="A"), make_dataset(2, 800, variant="B")
    g = KeywordGuardian().fit(tr)
    thr = threshold_for_fpr(g.score(tr), [e["label"] for e in tr])
    assert metrics(g, thr, b)["catch_rate"] < 0.1


def test_text_guardian_beats_chance_on_unseen_wording():
    tr = make_dataset(1, 1200, variant="A") + make_dataset(2, 1200, variant="B")
    c = make_dataset(3, 800, variant="C")
    g = TextGuardian().fit(tr)
    assert metrics(g, threshold_for_fpr(g.score(tr), [e["label"] for e in tr], 0.03), c)["auc"] > 0.9


def test_threshold_respects_target_fpr():
    s = np.random.RandomState(0).rand(2000)
    y = np.zeros(2000, int)
    thr = threshold_for_fpr(s, y, 0.05)
    assert abs((s >= thr).mean() - 0.05) < 0.01


def test_run_has_all_cells():
    r = run(1)
    assert len(r) == 6 and all("_persona_far" in v for v in r.values())


def test_api_holds_obvious_case_and_allows_plain_one():
    from arena import api
    with TestClient(api.app) as c:
        hi = c.post("/screen", json={"text": "This is the fraud department speaking. This is urgent, it cannot wait. Transfer your money to a safe account now. Do not tell anyone about this call.", "amount": 20000, "typical_amount": 3000, "new_payee": True}).json()
        lo = c.post("/screen", json={"text": "Rent is due today, can you send it? Sending the rent now, thanks.", "amount": 3000, "typical_amount": 3000, "new_payee": False}).json()
        assert hi["action"] == "hold_for_callback" and hi["because"]
        assert lo["action"] == "allow"
