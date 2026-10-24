"""Arena rounds. Scammers change wording when caught; the guardian retrains on what it has seen, never on the next wording.

Round 0: guardian trained on wording A, seen scam types.
Round 1: scammers switch to wording B. Guardian retrained on A+B.
Held out in both rounds: wording C, and the scam type tech_support (all wordings).
The alert threshold is set once per guardian on a validation set of legitimate conversations (3% false-alarm target)."""
import json

import numpy as np
from sklearn.metrics import roc_auc_score

from .guardian import ContextGuardian, KeywordGuardian, TextGuardian, threshold_for_fpr
from .scenarios import HELD_OUT_TYPES, PERSONAS, SEEN_TYPES, make_dataset

TARGET_FPR = 0.03
SEEDS = [1, 2, 3, 4, 5]


def metrics(g, thr, eps):
    s = g.score(eps)
    y = np.array([e["label"] for e in eps])
    flag = s >= thr
    scam_amt = sum(e["amount"] for e in eps if e["label"])
    return {"catch_rate": round(float(flag[y == 1].mean()), 3), "false_alarm_rate": round(float(flag[y == 0].mean()), 3),
            "money_protected": round(sum(e["amount"] for e, f in zip(eps, flag) if f and e["label"]) / max(1, scam_amt), 3),
            "auc": round(float(roc_auc_score(y, s)), 3)}


def per_persona_far(g, thr, eps):
    out = {}
    for p in PERSONAS:
        sub = [e for e in eps if e["persona"] == p and not e["label"]]
        out[p] = round(float((g.score(sub) >= thr).mean()), 3)
    return out


def run(seed):
    tr = {v: make_dataset(seed * 100 + i, 1200, variant=v) for i, v in enumerate("ABC")}
    val = make_dataset(seed * 100 + 50, 1200, variant="A") + make_dataset(seed * 100 + 51, 600, variant="B")
    tests = {
        "wording A (same as training)": make_dataset(seed * 100 + 60, 800, variant="A"),
        "wording B (switched)": make_dataset(seed * 100 + 61, 800, variant="B"),
        "wording C (never seen)": make_dataset(seed * 100 + 62, 800, variant="C"),
        "new scam type, wording C": make_dataset(seed * 100 + 63, 800, scam_types=HELD_OUT_TYPES, scam_rate=0.4, variant="C"),
    }
    # false alarms on legit conversations do not depend on wording; the held-out-type set reuses the same legit generator
    res = {}
    for rnd, train in (("round0", tr["A"]), ("round1", tr["A"] + tr["B"])):
        for G in (KeywordGuardian, ContextGuardian, TextGuardian):
            g = G().fit(train)
            vs = g.score(val)
            thr = threshold_for_fpr(vs, [e["label"] for e in val], TARGET_FPR)
            key = f"{rnd}/{g.name}"
            res[key] = {t: metrics(g, thr, eps) for t, eps in tests.items()}
            res[key]["_persona_far"] = per_persona_far(g, thr, sum(tests.values(), []))
    return res


def summarize(seeds=SEEDS):
    runs = [run(s) for s in seeds]
    agg = {}
    for key in runs[0]:
        agg[key] = {}
        for t in runs[0][key]:
            if t == "_persona_far":
                agg[key][t] = {p: round(float(np.mean([r[key][t][p] for r in runs])), 3) for p in PERSONAS}
            else:
                agg[key][t] = {m: round(float(np.mean([r[key][t][m] for r in runs])), 3) for m in runs[0][key][t]}
    agg["seeds"] = list(seeds)
    agg["target_false_alarm_rate"] = TARGET_FPR
    return agg


if __name__ == "__main__":
    out = summarize()
    print(json.dumps(out, indent=1))
    json.dump(out, open("results.json", "w"), indent=1)
