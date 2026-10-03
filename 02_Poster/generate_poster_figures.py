"""
Generates the two print-ready PNG figures for the IMC 2026 poster, from the
real, already-run Sionna simulation output (lmmse_results.json and
hybrid_ris_results.json) -- no illustrative or hand-tuned numbers.

Separate from the interactive demo's scripts (03_.../05_lmmse_comparison.py,
04_.../06_hybrid_ris_array_gain.py) on purpose: those write JSON for the
live dashboard, this reads that JSON and renders static, high-DPI PNGs for
print, which a browser artifact can't produce. Run this after re-running
those two scripts if the underlying numbers change.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

INK = "#1a1a1a"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"
BLUE = "#2a78d6"    # OFDM
ORANGE = "#eb6834"  # OTFS
GOOD = "#0ca30c"    # SENTRY's chosen operating point highlight

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 13,
    "text.color": INK,
    "axes.edgecolor": INK_SECONDARY,
    "axes.labelcolor": INK,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.9,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def fig1_otfs_vs_ofdm():
    with open("../03_Sionna_Simulation_OTFS/lmmse_results.json") as f:
        d = json.load(f)
    snr = d["snr_db"]
    ofdm = d["ofdm_ser"]
    otfs = d["otfs_ser"]

    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    ax.set_yscale("log")

    ax.plot(snr, ofdm, "-o", color=BLUE, linewidth=2.6, markersize=8,
             markeredgecolor="white", markeredgewidth=1.2, label="OFDM", zorder=3)
    ax.plot(snr, otfs, "-o", color=ORANGE, linewidth=2.6, markersize=8,
             markeredgecolor="white", markeredgewidth=1.2, label="OTFS", zorder=3)

    ax.axvspan(9, 15, color=ORANGE, alpha=0.08, zorder=0)
    ax.annotate("OTFS advantage\n(up to ~23% lower SER)",
                xy=(12, 0.078), xytext=(13.6, 0.20),
                fontsize=11, color=ORANGE, ha="left",
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.4))

    ax.set_xlabel("SNR (dB)", fontsize=13, labelpad=8)
    ax.set_ylabel("Symbol Error Rate (log scale)", fontsize=13, labelpad=8)
    ax.set_title("OTFS vs OFDM — Roadside NLOS Sensing Link", fontsize=16, fontweight="bold", pad=14)
    ax.text(0.5, 1.02, "SENTRY operating point: 100 km/h, 28 GHz · Sionna, TDL-A channel, MMSE equalization",
            transform=ax.transAxes, ha="center", fontsize=10.5, color=INK_SECONDARY)

    ax.minorticks_off()
    ax.set_yticks([0.05, 0.07, 0.1, 0.15, 0.2, 0.3, 0.4])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xticks(snr)
    ax.legend(frameon=False, fontsize=12.5, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, which="major", axis="both")

    fig.tight_layout()
    fig.savefig("poster_fig_otfs_vs_ofdm.png", dpi=300, bbox_inches="tight")
    print("Saved poster_fig_otfs_vs_ofdm.png")
    plt.close(fig)


def fig2_hybrid_ris_gain():
    with open("../04_Sionna_SimuLltion_HYBRID_RIS/hybrid_ris_results.json") as f:
        d = json.load(f)
    frac_pct = [f * 100 for f in d["fraction"]]
    gain = d["gain_db"]
    passive_gain = gain[0]

    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)

    ax.axhline(passive_gain, color=INK_SECONDARY, linewidth=1.2, linestyle="--", zorder=1)
    ax.text(72, passive_gain + 0.8, f"Passive-only baseline: {passive_gain:.1f} dB",
            fontsize=10.5, color=INK_SECONDARY, ha="left")

    ax.plot(frac_pct, gain, "-o", color=BLUE, linewidth=2.6, markersize=7,
            markeredgecolor="white", markeredgewidth=1.1, zorder=3)

    idx8 = d["fraction"].index(0.08)
    ax.scatter([frac_pct[idx8]], [gain[idx8]], s=170, color=GOOD, zorder=5,
               edgecolor="white", linewidth=1.6)
    ax.annotate(f"SENTRY's hybrid design\n8% active → {gain[idx8]:.1f} dB\n(+{d['gain_over_passive_db'][idx8]:.1f} dB over passive)",
                xy=(8, gain[idx8]), xytext=(30, 45.8),
                fontsize=11, color=GOOD, ha="left", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=GOOD, lw=1.4))

    ax.set_xlabel("Active elements (% of 128-element array)", fontsize=13, labelpad=8)
    ax.set_ylabel("Array gain toward hazard (dB)", fontsize=13, labelpad=8)
    ax.set_title("Hybrid RIS — Gain vs. Active-Element Fraction", fontsize=16, fontweight="bold", pad=14)
    ax.text(0.5, 1.02, "128-element linear RIS, 28 GHz, half-wavelength spacing, 1-bit passive phase quantization",
            transform=ax.transAxes, ha="center", fontsize=10.5, color=INK_SECONDARY)

    ax.set_xlim(-3, 103)
    ax.set_ylim(37, 55.5)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig("poster_fig_hybrid_ris_gain.png", dpi=300, bbox_inches="tight")
    print("Saved poster_fig_hybrid_ris_gain.png")
    plt.close(fig)


if __name__ == "__main__":
    fig1_otfs_vs_ofdm()
    fig2_hybrid_ris_gain()
