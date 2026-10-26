"""More README figures, drawn from results_extra.json. Run: python -m arena.extras && python -m arena.figures_extra"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .report import COLORS, GRID, INK, MUTED, OUT, _style  # noqa: E402
from .scenarios import TACTICS  # noqa: E402

TYPE_LABELS = {"bank_impersonation": "Bank\nimpersonation", "investment": "Investment", "romance": "Romance",
               "invoice_redirect": "Invoice\nredirect", "tech_support": "Tech support\n(held out)"}
WORDING_COLORS = {"A": "#ef4444", "B": "#f59e0b", "C": "#6366f1"}


def tradeoff(ex: dict, path: Path) -> None:
    t = ex["tradeoff_wording_C"]
    xs = [f * 100 for f in t["false_alarm_grid"]]
    fig, ax = plt.subplots(figsize=(9, 5), dpi=160)
    for name, color in (("keyword rules", COLORS["keyword rules"]), ("payment context only", COLORS["payment context only"]),
                        ("text + context model", COLORS["retrained"])):
        ax.plot(xs, [v * 100 for v in t[name]], "-o", color=color, lw=3, ms=7, label=name)
    ax.axvline(3, color=GRID, lw=6, zorder=0)
    ax.text(3.2, 4, "operating\npoint (3%)", color=MUTED, fontsize=9)
    ax.set_xlabel("False-alarm rate allowed on validation data (%)", color=MUTED)
    ax.set_ylabel("Scams caught on unseen wording C (%)", color=MUTED)
    ax.set_title("What does each extra point of caution buy?", loc="left", color=INK, fontsize=15, fontweight="bold", pad=16)
    ax.set_ylim(-3, 103)
    _style(ax)
    ax.legend(frameon=False, loc="center right", labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def by_type(ex: dict, path: Path) -> None:
    d = ex["catch_by_scam_type_text_round1_wording_C"]
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=160)
    vals = [d[k] * 100 for k in TYPE_LABELS]
    bars = ax.bar(list(TYPE_LABELS.values()), vals, color=["#6366f1"] * 4 + ["#10b981"], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}%", ha="center", color=INK, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Scams caught (%)", color=MUTED)
    ax.set_title("Catch rate by scam type (retrained text model, wording C)", loc="left", color=INK, fontsize=14, fontweight="bold", pad=16)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def score_spread(ex: dict, path: Path) -> None:
    s = ex["score_spread"]
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
    bins = np.linspace(0, 1, 26)
    ax.hist(s["honest"], bins=bins, color="#10b981", alpha=0.85, label="Honest payments")
    ax.hist(s["scam"], bins=bins, color="#ef4444", alpha=0.75, label="Scams")
    ax.set_yscale("log")
    ax.set_xlabel("Risk score from the text + context model", color=MUTED)
    ax.set_ylabel("Conversations (log scale, sample of 600 each)", color=MUTED)
    ax.set_title("Where the scores land", loc="left", color=INK, fontsize=15, fontweight="bold", pad=16)
    _style(ax)
    ax.legend(frameon=False, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def wording_sets(path: Path) -> None:
    tactics = ["urgency", "secrecy", "move_money"]
    fig, ax = plt.subplots(figsize=(12, 5.4), dpi=160)
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(-0.3, 5.4)
    ax.text(0.1, 5.05, "Same warning sign, three ways to say it", fontsize=15, fontweight="bold", color=INK)
    for row, tactic in enumerate(tactics):
        y = 3.55 - row * 1.55
        ax.text(0.1, y + 0.55, tactic.replace("_", " ").upper(), fontsize=9, color=MUTED, fontweight="bold")
        for col, v in enumerate("ABC"):
            x = 0.1 + col * 3.95
            ax.add_patch(plt.Rectangle((x, y - 0.55), 3.75, 1.0, fc="white", ec=WORDING_COLORS[v], lw=2.5))
            phrase = TACTICS[tactic][v][0]
            words, lines, cur = phrase.split(), [], ""
            for w in words:
                if len(cur) + len(w) > 34:
                    lines.append(cur)
                    cur = ""
                cur = f"{cur} {w}".strip()
            lines.append(cur)
            ax.text(x + 0.12, y - 0.05, "\n".join(lines), fontsize=9.5, color=INK, va="center")
            if row == 0:
                label = {"A": "A: common (trained on)", "B": "B: what scammers switch to", "C": "C: never trained on"}[v]
                ax.text(x, y + 0.82, label, fontsize=10, fontweight="bold", color=WORDING_COLORS[v])
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ex = json.load(open("results_extra.json"))
    OUT.mkdir(parents=True, exist_ok=True)
    tradeoff(ex, OUT / "tradeoff.png")
    by_type(ex, OUT / "by_scam_type.png")
    score_spread(ex, OUT / "score_spread.png")
    wording_sets(OUT / "wording_sets.png")
    print("wrote tradeoff, by_scam_type, score_spread, wording_sets")


if __name__ == "__main__":
    main()
