"""Charts from results/summary.json. Titles state the sample size that was actually saved."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = _ROOT
RESULTS = ROOT / "results"
IMAGES = ROOT / "images"
SUMMARY = RESULTS / "summary.json"

BLUE = "#0072B2"
ORANGE = "#E69F00"
COLORS = {"tests-first": BLUE, "code-only": ORANGE}


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
        }
    )


def _load() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def chart_pass_rates(summary: dict) -> Path:
    _style()
    conditions = ["tests-first", "code-only"]
    labels = ["tests-first", "code-only"]
    full = [summary["conditions"][c]["full_pass_rate"] or 0 for c in conditions]
    full_low = [summary["conditions"][c]["full_pass_wilson95"]["low"] or 0 for c in conditions]
    full_high = [summary["conditions"][c]["full_pass_wilson95"]["high"] or 0 for c in conditions]
    mean_f = [summary["conditions"][c]["fraction"]["mean"] or 0 for c in conditions]
    frac_low = [summary["conditions"][c]["fraction"]["low"] or 0 for c in conditions]
    frac_high = [summary["conditions"][c]["fraction"]["high"] or 0 for c in conditions]
    ns = [summary["conditions"][c]["n"] for c in conditions]
    n_label = ", ".join(f"{c} n={n}" for c, n in zip(conditions, ns))

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4), sharey=True)
    x = np.arange(2)
    for ax, values, lows, highs, title, ylab in (
        (
            axes[0],
            full,
            full_low,
            full_high,
            "Full hidden-suite pass",
            "Rate",
        ),
        (
            axes[1],
            mean_f,
            frac_low,
            frac_high,
            "Mean fraction of hidden tests passed",
            "Fraction",
        ),
    ):
        yerr = np.vstack([np.array(values) - np.array(lows), np.array(highs) - np.array(values)])
        ax.bar(x, values, color=[COLORS[c] for c in conditions], width=0.72, zorder=2)
        ax.errorbar(x, values, yerr=yerr, fmt="none", ecolor="black", capsize=4, zorder=3)
        ax.set_xticks(x, labels)
        ax.set_ylim(0, 1)
        ax.set_title(title)
        ax.set_ylabel(ylab)
        for i, value in enumerate(values):
            ax.text(i, min(0.97, value + 0.04), f"{value:.2f}", ha="center", va="bottom", fontsize=10)
    fig.suptitle(f"Grok 4.7 on author-written tasks ({n_label})", fontsize=12)
    fig.tight_layout()
    path = IMAGES / "pass_rate_by_condition.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def chart_heatmap(summary: dict) -> Path:
    _style()
    runs = summary["runs"]
    tasks = []
    for run in runs:
        if run["task_id"] not in tasks:
            tasks.append(run["task_id"])
    conditions = ["tests-first", "code-only"]
    # Average across reps when a second repetition exists. The title says so.
    reps = summary.get("reps") or []
    grid = np.full((len(tasks), len(conditions)), np.nan)
    for i, task in enumerate(tasks):
        for j, condition in enumerate(conditions):
            vals = [
                float(run["fraction"] or 0.0)
                for run in runs
                if run["task_id"] == task and run["condition"] == condition and run["fraction"] is not None
            ]
            if vals:
                grid[i, j] = sum(vals) / len(vals)
    fig_h = max(4.2, 0.42 * len(tasks) + 1.6)
    fig, ax = plt.subplots(figsize=(6.4, fig_h))
    image = ax.imshow(grid, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(conditions)), conditions)
    ax.set_yticks(range(len(tasks)), tasks)
    for i in range(len(tasks)):
        for j in range(len(conditions)):
            value = grid[i, j]
            if np.isnan(value):
                label = "—"
                color = "black"
            else:
                label = f"{value:.2f}"
                color = "white" if value < 0.55 else "black"
            ax.text(j, i, label, ha="center", va="center", color=color, fontsize=10)
    fig.colorbar(image, ax=ax, label="Fraction of hidden tests passed")
    rep_note = "mean across reps" if len(reps) > 1 else "1 run per cell"
    ax.set_title(f"Hidden-test fraction by task ({rep_note}, n_runs={summary['n_runs']})")
    fig.tight_layout()
    path = IMAGES / "per_task_heatmap.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def chart_cost(summary: dict) -> Path:
    _style()
    runs = summary["runs"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4))
    rng = np.random.default_rng(0)
    for ax, field, title, ylabel in (
        (axes[0], "wall_seconds", "Wall time of the scored attempt", "Seconds"),
        (axes[1], "output_tokens", "Output tokens, scored attempt", "Output tokens"),
    ):
        for index, condition in enumerate(("tests-first", "code-only")):
            values = [run[field] for run in runs if run["condition"] == condition and run[field] is not None]
            xs = rng.normal(index, 0.04, size=len(values))
            ax.scatter(xs, values, color=COLORS[condition], s=36, zorder=3, label=condition if ax is axes[0] else None)
            if values:
                med = float(np.median(values))
                ax.hlines(med, index - 0.22, index + 0.22, colors="black", linewidths=1.5, zorder=4)
        ax.set_xticks([0, 1], ["tests-first", "code-only"])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        axes[0].legend(frameon=False, loc="best")
    n = summary["n_runs"]
    fig.suptitle(
        f"Time and output tokens by condition (points are runs, bars are medians, n={n})",
        fontsize=12,
    )
    fig.tight_layout()
    path = IMAGES / "time_tokens.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    summary = _load()
    if summary["n_runs"] == 0:
        print("no runs, no charts")
        return
    paths = [chart_pass_rates(summary), chart_heatmap(summary), chart_cost(summary)]
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
