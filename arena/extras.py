"""Extra analysis behind the figures and the audit: per-scam-type catch, realised false-alarm rates, score spread and
the catch-versus-false-alarm trade-off. Same data and seeds as evaluate.py. Run: python -m arena.extras"""
import json

import numpy as np

from .evaluate import SEEDS, TARGET_FPR
from .guardian import ContextGuardian, KeywordGuardian, TextGuardian, threshold_for_fpr
from .scenarios import HELD_OUT_TYPES, SCAM_TYPES, make_dataset

GUARDIANS = (KeywordGuardian, ContextGuardian, TextGuardian)
FPR_GRID = [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.2]


def _fit_round1(seed: int):
    tr = make_dataset(seed * 100, 1200, variant="A") + make_dataset(seed * 100 + 1, 1200, variant="B")
    val = make_dataset(seed * 100 + 50, 1200, variant="A") + make_dataset(seed * 100 + 51, 600, variant="B")
    return tr, val, [e["label"] for e in val]


def analyse(seeds=SEEDS) -> dict:
    by_type = {t: [] for t in SCAM_TYPES}
    far_cells = {}
    curves = {G.name: np.zeros(len(FPR_GRID)) for G in GUARDIANS}
    spread = {"scam": [], "honest": []}
    for seed in seeds:
        tr, val, vy = _fit_round1(seed)
        c_seen = make_dataset(seed * 100 + 62, 800, variant="C")
        c_new = make_dataset(seed * 100 + 63, 800, scam_types=HELD_OUT_TYPES, scam_rate=0.4, variant="C")
        a_test = make_dataset(seed * 100 + 60, 800, variant="A")
        b_test = make_dataset(seed * 100 + 61, 800, variant="B")
        for G in GUARDIANS:
            g = G().fit(tr)
            thr = threshold_for_fpr(g.score(val), vy, TARGET_FPR)
            for name, eps in (("A", a_test), ("B", b_test), ("C", c_seen), ("new type", c_new)):
                s = g.score(eps)
                y = np.array([e["label"] for e in eps])
                far_cells.setdefault(f"{g.name}/{name}", []).append(float((s[y == 0] >= thr).mean()))
            if G is TextGuardian:
                s, eps = g.score(c_seen + c_new), c_seen + c_new
                for e, sc in zip(eps, s):
                    if e["label"]:
                        by_type[e["kind"]].append(float(sc >= thr))
                y = np.array([e["label"] for e in eps])
                spread["scam"] += list(s[y == 1])
                spread["honest"] += list(s[y == 0])
            s_c, y_c = g.score(c_seen), np.array([e["label"] for e in c_seen])
            for i, f in enumerate(FPR_GRID):
                t = threshold_for_fpr(g.score(val), vy, f)
                curves[g.name][i] += float((s_c[y_c == 1] >= t).mean()) / len(seeds)
    return {"seeds": list(seeds),
            "catch_by_scam_type_text_round1_wording_C": {t: round(float(np.mean(v)), 3) for t, v in by_type.items() if v},
            "realised_false_alarm_rate": {k: round(float(np.mean(v)), 3) for k, v in far_cells.items()},
            "tradeoff_wording_C": {"false_alarm_grid": FPR_GRID, **{k: [round(x, 3) for x in v] for k, v in curves.items()}},
            "score_spread": {k: [round(float(x), 4) for x in np.random.RandomState(0).choice(v, 600)] for k, v in spread.items()}}


if __name__ == "__main__":
    out = analyse()
    json.dump(out, open("results_extra.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "score_spread"}, indent=1))
