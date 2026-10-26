"""Draws the README figures from results.json. Run: python -m arena.report"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = Path("docs/img")
INK, MUTED, GRID = "#0f172a", "#64748b", "#e2e8f0"
COLORS = {"keyword rules": "#ef4444", "payment context only": "#f59e0b", "text + context model": "#6366f1", "retrained": "#10b981"}
SCENARIOS = ["wording A (same as training)", "wording B (switched)", "wording C (never seen)", "new scam type, wording C"]
SHORT = ["Wording A\n(trained)", "Wording B\n(scammers switch)", "Wording C\n(never seen)", "New scam type\n(never seen)"]
PERSONA_LABELS = {"older_cautious": "Older &\ncautious", "young_busy": "Young &\nbusy", "small_business": "Small\nbusiness", "new_to_country": "New to\nthe country"}


def _style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def _series(res: dict) -> list[tuple[str, str, str]]:
    return [("Keyword rules", "round1/keyword rules", COLORS["keyword rules"]),
            ("Payment context only", "round1/payment context only", COLORS["payment context only"]),
            ("Text + context (round 0)", "round0/text + context model", COLORS["text + context model"]),
            ("Text + context (retrained)", "round1/text + context model", COLORS["retrained"])]


def arms_race(res: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=160)
    label_nudge = {"Payment context only": 6, "Text + context (round 0)": -6}  # keep end labels from overlapping
    for label, key, color in _series(res):
        ys = [res[key][s]["catch_rate"] * 100 for s in SCENARIOS]
        ax.plot(range(4), ys, "-o", color=color, lw=3, ms=9, label=label)
        ax.annotate(f"{ys[-1]:.0f}%", (3, ys[-1]), xytext=(12, label_nudge.get(label, 0)), textcoords="offset points", va="center", color=color, fontweight="bold")
    ax.set_xticks(range(4), SHORT, color=INK)
    ax.set_ylim(-3, 105)
    ax.set_xlim(-0.2, 3.5)
    ax.set_ylabel("Scams caught (%) at about 3% false alarms", color=MUTED)
    ax.set_title("The arms race: what happens when scammers change their words", loc="left", color=INK, fontsize=15, fontweight="bold", pad=16)
    _style(ax)
    ax.legend(frameon=False, loc="lower left", labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fairness(res: dict, path: Path) -> None:
    far = res["round1/text + context model"]["_persona_far"]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
    names = list(far)
    vals = [far[n] * 100 for n in names]
    bars = ax.bar([PERSONA_LABELS[n] for n in names], vals, color="#6366f1", width=0.55)
    ax.axhline(res["target_false_alarm_rate"] * 100, color="#ef4444", ls="--", lw=1.5)
    ax.text(3.45, res["target_false_alarm_rate"] * 100 + 0.08, "3% target", color="#ef4444", ha="right", fontsize=9)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.06, f"{v:.1f}%", ha="center", color=INK, fontweight="bold")
    ax.set_ylim(0, 4)
    ax.set_ylabel("Honest payments wrongly held (%)", color=MUTED)
    ax.set_title("False alarms by customer group (retrained text model)", loc="left", color=INK, fontsize=15, fontweight="bold", pad=16)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def pipeline(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 3.6), dpi=160)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3.6)
    ax.axis("off")
    boxes = [("Scripted scammer", "5 scam types\nA/B/C wording", "#fee2e2", "#ef4444"),
             ("Conversation +\npayment", "text, amount,\nnew payee", "#e0e7ff", "#6366f1"),
             ("Guardian", "rules, context,\ntext model", "#ede9fe", "#7c3aed"),
             ("Allow or hold\nfor call-back", "human checks,\ncustomer never accused", "#d1fae5", "#10b981")]
    for i, (title, sub, fill, edge) in enumerate(boxes):
        x = 0.3 + i * 2.75
        ax.add_patch(FancyBboxPatch((x, 1.0), 2.2, 1.9, boxstyle="round,pad=0.05,rounding_size=0.2", fc=fill, ec=edge, lw=2))
        ax.text(x + 1.1, 2.35, title, ha="center", va="center", fontsize=11, fontweight="bold", color=INK)
        ax.text(x + 1.1, 1.55, sub, ha="center", va="center", fontsize=9, color=MUTED)
        if i < 3:
            ax.annotate("", xy=(x + 2.7, 1.95), xytext=(x + 2.25, 1.95), arrowprops=dict(arrowstyle="-|>", color=INK, lw=2))
    ax.plot([9.4, 9.4, 1.4], [1.0, 0.55, 0.55], color="#f59e0b", lw=2)
    ax.annotate("", xy=(1.4, 1.0), xytext=(1.4, 0.55), arrowprops=dict(arrowstyle="-|>", color="#f59e0b", lw=2))
    ax.text(5.5, 0.12, "Round 1: retrain on the wording scammers just used", ha="center", color="#b45309", fontsize=10, fontweight="bold")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    res = json.load(open("results.json"))
    OUT.mkdir(parents=True, exist_ok=True)
    arms_race(res, OUT / "arms_race.png")
    fairness(res, OUT / "fairness.png")
    pipeline(OUT / "pipeline.png")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
