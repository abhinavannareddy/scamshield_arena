"""Screening service: given a conversation and a payment, say allow or hold-for-callback."""
from fastapi import FastAPI
from pydantic import BaseModel

from .guardian import TextGuardian, explain, threshold_for_fpr
from .scenarios import make_dataset

app = FastAPI(title="ScamShield Arena")
_s = {}


class Screen(BaseModel):
    text: str
    amount: float
    typical_amount: float = 3000
    new_payee: bool = True


@app.on_event("startup")
def startup():
    train = make_dataset(1, 1200, variant="A") + make_dataset(2, 1200, variant="B")
    val = make_dataset(3, 1200, variant="A") + make_dataset(4, 600, variant="B")
    g = TextGuardian().fit(train)
    _s.update(g=g, thr=threshold_for_fpr(g.score(val), [e["label"] for e in val], 0.03))


@app.post("/screen")
def screen(b: Screen):
    ep = {"text": b.text, "amount": b.amount, "typical": b.typical_amount, "new_payee": int(b.new_payee)}
    sc = float(_s["g"].score([ep])[0])
    hold = sc >= _s["thr"]
    return {"action": "hold_for_callback" if hold else "allow", "score": round(sc, 3), "threshold": round(_s["thr"], 3),
            "because": explain(_s["g"], ep) if hold else [],
            "note": "The customer is never accused. A hold means a human checks with the customer before money moves."}
