"""
One palette and one set of chart chrome, shared by every figure in the repo.

Kept here rather than copied into each script so the charts in docs/img/ cannot
drift apart visually. Colours are a colour-blind-safe set; blue and orange are
the two series hues and are distinguishable under deuteranopia.
"""
import matplotlib
matplotlib.use("Agg")                      # no display on a CI runner
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

SURFACE  = "#fcfcfb"
INK      = "#0b0b0b"
INK_2    = "#52514e"
MUTED    = "#898781"
GRID     = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE     = "#2a78d6"
ORANGE   = "#eb6834"
RED      = "#d03b3b"

PCT = FuncFormatter(lambda v, _: f"{v:.0%}")


def apply():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "font.size": 10,
        "font.family": "DejaVu Sans",
        "axes.edgecolor": BASELINE, "axes.labelcolor": INK_2,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.titlecolor": INK, "axes.titlesize": 12,
        "axes.titleweight": "semibold", "axes.titlelocation": "left",
        "axes.titlepad": 14,
    })


def style(ax, ygrid=True, xgrid=False):
    """Recessive chrome: no box, hairline grid on the measured axis only."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_axisbelow(True)
    if ygrid:
        ax.grid(axis="y", color=GRID, linewidth=0.8)
    if xgrid:
        ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.tick_params(length=0)


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path.name:<34}{path.stat().st_size // 1024:>5} KB")
