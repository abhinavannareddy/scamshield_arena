"""Screening service: given a conversation and a payment, say allow or hold-for-callback."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .guardian import TextGuardian, explain, threshold_for_fpr
from .scenarios import make_dataset

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
FALSE_ALARM_TARGET = 0.03
_state: dict = {}


class Screen(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    amount: float = Field(gt=0, le=1e9)
    typical_amount: float = Field(default=3000, gt=0, le=1e9)
    new_payee: bool = True


@asynccontextmanager
async def lifespan(_: FastAPI):
    train = make_dataset(1, 1200, variant="A") + make_dataset(2, 1200, variant="B")
    val = make_dataset(3, 1200, variant="A") + make_dataset(4, 600, variant="B")
    guardian = TextGuardian().fit(train)
    threshold = threshold_for_fpr(guardian.score(val), [e["label"] for e in val], FALSE_ALARM_TARGET)
    _state.update(g=guardian, thr=threshold)
    yield
    _state.clear()


app = FastAPI(title="ScamShield Arena", lifespan=lifespan)
app.mount("/img", StaticFiles(directory=ROOT / "docs" / "img", check_dir=False), name="img")


@app.get("/", include_in_schema=False)
def demo() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_ready": "g" in _state}


@app.post("/screen")
def screen(b: Screen) -> dict:
    ep = {"text": b.text, "amount": b.amount, "typical": b.typical_amount, "new_payee": int(b.new_payee)}
    score = float(_state["g"].score([ep])[0])
    hold = score >= _state["thr"]
    return {"action": "hold_for_callback" if hold else "allow", "score": round(score, 3), "threshold": round(_state["thr"], 3),
            "because": explain(_state["g"], ep) if hold else [],
            "note": "The customer is never accused. A hold means a human checks with the customer before money moves."}
