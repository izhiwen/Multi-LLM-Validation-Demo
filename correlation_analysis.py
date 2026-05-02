"""
correlation_analysis.py
-----------------------
Compute and plot the pairwise correlation matrix of LLM-assigned scores
for the multi-model validation backbone described in the README.

Input  : data/llm_scores_aggregated.csv  (one row per document, one column per model)
Output : figures/multi_llm_correlation_heatmap.png  (publication-style heatmap)
         figures/multi_llm_correlation_heatmap_bw.png  (black-and-white version)

Author : Steve Zhiwen Wang  (zhw94@pitt.edu)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


SCORE_COLS = [
    "chatgpt_score",
    "gemini_score",
    "claude_score",
    "qwen_score",
    "deepseek_score",
]
DISPLAY_NAMES = ["ChatGPT", "Gemini", "Claude", "Qwen", "DeepSeek"]

REPO_ROOT = Path(__file__).resolve().parent
DATA_PATH = REPO_ROOT / "data" / "llm_scores_aggregated.csv"
FIG_DIR = REPO_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)


def _adjust_alpha(hex_color: str, alpha: float) -> str:
    """Blend a hex color with white to simulate transparency without alpha channels."""
    rgb = mcolors.hex2color(hex_color)
    blended = tuple(alpha * c + (1.0 - alpha) * 1.0 for c in rgb)
    return mcolors.rgb2hex(blended)


def _build_colormaps() -> tuple[LinearSegmentedColormap, LinearSegmentedColormap]:
    stata_maroon = "#90353b"
    color_list = [
        "#ffffff",
        _adjust_alpha(stata_maroon, 0.10),
        _adjust_alpha(stata_maroon, 0.25),
        _adjust_alpha(stata_maroon, 0.42),
        _adjust_alpha(stata_maroon, 0.60),
        _adjust_alpha(stata_maroon, 0.78),
        _adjust_alpha(stata_maroon, 0.92),
    ]
    bw_list = [
        "#ffffff",
        "#eeeeee",
        "#dddddd",
        "#bbbbbb",
        "#888888",
        "#555555",
        "#222222",
    ]
    return (
        LinearSegmentedColormap.from_list("custom_maroon", color_list),
        LinearSegmentedColormap.from_list("custom_greys", bw_list),
    )


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    return df[SCORE_COLS].corr()


def plot_heatmap(corr: pd.DataFrame, cmap, output_path: Path, title: str) -> None:
    """Render a correlation heatmap with academic-journal styling."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 11,
            "axes.linewidth": 0.8,
            "axes.edgecolor": "#333333",
        }
    )
    fig, ax = plt.subplots(figsize=(6.0, 5.2), dpi=200)
    mask = np.eye(len(SCORE_COLS), dtype=bool)
    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        vmin=0.5,
        vmax=1.0,
        cbar=True,
        cbar_kws={"shrink": 0.8, "pad": 0.02, "label": "Pairwise correlation"},
        xticklabels=DISPLAY_NAMES,
        yticklabels=DISPLAY_NAMES,
        linewidths=0.5,
        linecolor="#dddddd",
        square=True,
        ax=ax,
    )
    ax.set_title(title, fontsize=12, pad=12)
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} documents.")

    corr = compute_correlations(df)
    print("\nPairwise correlation matrix:")
    print(corr.round(3))
    off_diag = corr.values[~np.eye(len(SCORE_COLS), dtype=bool)]
    print(
        f"\nOff-diagonal range: [{off_diag.min():.3f}, {off_diag.max():.3f}]"
        f"  (mean = {off_diag.mean():.3f})"
    )

    color_cmap, bw_cmap = _build_colormaps()
    plot_heatmap(
        corr,
        color_cmap,
        FIG_DIR / "multi_llm_correlation_heatmap.png",
        "Pairwise score correlation across five frontier LLMs (N = 294 documents)",
    )
    plot_heatmap(
        corr,
        bw_cmap,
        FIG_DIR / "multi_llm_correlation_heatmap_bw.png",
        "Pairwise score correlation across five frontier LLMs (N = 294 documents)",
    )
    print(f"\nFigures written to {FIG_DIR}.")


if __name__ == "__main__":
    main()
