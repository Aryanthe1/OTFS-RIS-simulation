"""
Poster "photo" figures -- a real-time scenario look (top-down road diagram,
radar-style beam lock), not a line/data chart. Same real Sionna and
array-factor numbers as the interactive demo (05_Live_Demo/index.html) and
generate_poster_figures.py, just rendered as a scenario illustration
instead of a plotted curve, per direct feedback that the line-chart PNGs
weren't the right visual for this poster slot.

Reuses the exact same scene geometry (SCENE units, 1000x400) as the HTML
demo's road diagram, so the printed poster and the live booth demo show
the same layout -- not a coincidence, a deliberate consistency check.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, PathPatch
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
from matplotlib.colors import LinearSegmentedColormap

BG = "#f7f8fa"
PANEL = "#ffffff"
ROAD = "#c9ced6"
ROAD_EDGE = "#828b9a"
BUILDING = "#e3e6ec"
BORDER = "#c7cdd6"
INK = "#12151c"
INK_2 = "#3f4552"
INK_MUTED = "#5b6472"
ACCENT = "#2a78d6"
ACCENT_2 = "#c2540a"
GOOD = "#0ca30c"
WARNING = "#e0980a"
SERIOUS = "#d96b3f"
CRITICAL = "#c62f2f"

STATUS_CMAP = LinearSegmentedColormap.from_list("status", [GOOD, WARNING, SERIOUS, CRITICAL])

plt.rcParams.update({
    "font.family": "sans-serif",
    "text.color": INK,
})

SCENE = dict(start=40, detect=430, los=800, end=940, laneY=290,
             building=(660, 120, 140, 130), cross=(800, 0, 80, 252),
             road=(0, 250, 1000, 80), rsu=(788, 244), hazard=(838, 56))
METERS_PER_UNIT = 0.12


def draw_base_scene(ax):
    ax.set_facecolor(BG)
    ax.add_patch(Rectangle((0, 0), 1000, 400, color=BG, zorder=0))
    cx, cy, cw, ch = SCENE["cross"]
    ax.add_patch(Rectangle((cx, cy), cw, ch, color=ROAD, zorder=1))
    ax.plot([840, 840], [0, 252], color=ROAD_EDGE, lw=1.5, ls=(0, (10, 8)), zorder=2)
    rx, ry, rw, rh = SCENE["road"]
    ax.add_patch(Rectangle((rx, ry), rw, rh, color=ROAD, zorder=1))
    ax.plot([0, 1000], [290, 290], color=ROAD_EDGE, lw=1.5, ls=(0, (14, 10)), zorder=2)
    bx, by, bw, bh = SCENE["building"]
    ax.add_patch(Rectangle((bx, by), bw, bh, color=BUILDING, ec=BORDER, lw=1, zorder=3))
    ax.text(bx + bw / 2, by + 34, "BUILDING", color=INK_MUTED, ha="center",
            fontsize=10, family="monospace", zorder=4)
    ax.text(bx + bw / 2, by + 50, "(blocks sightline)", color=INK_MUTED, ha="center",
            fontsize=8.5, family="monospace", zorder=4)

    rsu_x, rsu_y = SCENE["rsu"]
    ax.plot([rsu_x, rsu_x], [rsu_y, rsu_y + 30], color=INK_MUTED, lw=3, zorder=5)
    panel = Rectangle((-10, 0), 20, 46, facecolor=PANEL, edgecolor=ACCENT, lw=1.6, zorder=6)
    panel.set_transform(Affine2D().rotate_deg(-18).translate(rsu_x, rsu_y) + ax.transData)
    ax.add_patch(panel)
    ax.text(rsu_x - 34, rsu_y + 30, "RSU + RIS", color=ACCENT, ha="right", fontsize=9.5,
            family="monospace", zorder=6)

    hx, hy = SCENE["hazard"]
    ax.add_patch(Circle((hx, hy), 8, color=CRITICAL, zorder=7))
    ax.add_patch(Circle((hx, hy), 15, color=CRITICAL, alpha=0.25, zorder=6))
    ax.text(hx, hy - 20, "PEDESTRIAN", color=CRITICAL, ha="center", fontsize=9.5,
            family="monospace", zorder=7)

    ax.set_xlim(-25, 1025)
    ax.set_ylim(430, -45)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_car(ax, x, y, color, flip=False):
    w, h = 34, 18
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=color, edgecolor="none",
                            zorder=8, joinstyle="round"))
    ax.add_patch(Rectangle((x - w / 2 + 6, y - h / 2 + 3), 12, h - 6, facecolor=BG, alpha=0.5, zorder=9))


def draw_error_grid(ax, grid_2d, title, xlabel, ylabel, ser_value, ser_color, vmax):
    """A print version of the same real per-cell error-rate grid the HTML
    demo renders live -- transpose/axis convention matches it exactly
    (see 05_Live_Demo/index.html's renderGrid/transpose)."""
    im = ax.imshow(grid_2d, cmap=STATUS_CMAP, vmin=0, vmax=vmax, origin="lower",
                    aspect="equal", interpolation="nearest")
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=INK, fontsize=13.5, fontweight="bold", pad=34, family="monospace")
    ax.text(0.5, 1.06, f"Symbol Error Rate: {ser_value*100:.1f}%", transform=ax.transAxes,
            ha="center", va="bottom", color=ser_color, fontsize=12.5, fontweight="bold",
            family="monospace")
    ax.set_xlabel(xlabel, color=INK_MUTED, fontsize=9.5, family="monospace", labelpad=6)
    ax.set_ylabel(ylabel, color=INK_MUTED, fontsize=9.5, family="monospace", labelpad=6)
    ax.set_xticks([0, 31]); ax.set_xticklabels(["0", "31"])
    ax.set_yticks([0, 31]); ax.set_yticklabels(["0", "31"])
    ax.tick_params(colors=INK_MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    return im


def fig_otfs_vs_ofdm():
    with open("../03_Sionna_Simulation_OTFS/grid_domain_snapshots.json") as f:
        gd = json.load(f)
    idx100 = gd["speeds_kmh"].index(100)
    ofdm_ser = gd["ofdm_ser"][idx100]
    otfs_ser = gd["otfs_ser"][idx100]
    ofdm_grid = np.array(gd["ofdm_error_grid"][idx100]).T   # transpose: time on x, freq on y (matches HTML)
    otfs_grid = np.array(gd["otfs_error_grid"][idx100])     # delay on x, Doppler on y already
    grid_vmax = max(ofdm_grid.max(), otfs_grid.max())

    speed_kmh = 100.0
    speed_ms = speed_kmh / 3.6
    extra_dist = (SCENE["los"] - SCENE["detect"]) * METERS_PER_UNIT
    extra_time = extra_dist / speed_ms

    fig = plt.figure(figsize=(11, 11.8), dpi=300)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.32, wspace=0.32,
                           top=0.94, bottom=0.14, left=0.08, right=0.95)
    ax = fig.add_subplot(gs[0, :])
    draw_base_scene(ax)

    # sensing beam, bent around the building corner (same curve validated in the HTML demo)
    beam_path = Path([(782, 206), (862, 158), (838, 63)],
                      [Path.MOVETO, Path.CURVE3, Path.CURVE3])
    ax.add_patch(PathPatch(beam_path, facecolor="none", edgecolor=GOOD, lw=2.6,
                            linestyle=(0, (7, 8)), zorder=6))

    # car at the moment SENTRY alerts (well before the building)
    draw_car(ax, SCENE["detect"], SCENE["laneY"], INK)
    ax.plot([SCENE["detect"], SCENE["detect"]], [250, 330], color=ACCENT_2, lw=1.5, ls=(0, (4, 5)), zorder=4)
    ax.annotate("SENTRY ALERT SENT", xy=(SCENE["detect"], 240), xytext=(SCENE["detect"], 178),
                color=ACCENT_2, fontsize=12, fontweight="bold", ha="center", family="monospace",
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_2, lw=1.6))

    # ghost car at the point a human would first get a sightline
    draw_car(ax, SCENE["los"], SCENE["laneY"], INK_MUTED)
    ax.plot([SCENE["los"], SCENE["los"]], [250, 330], color=INK_MUTED, lw=1.5, ls=(0, (4, 5)), zorder=4)
    ax.text(SCENE["los"], 345, "unaided sightline", color=INK_2, fontsize=9.5, ha="center",
            family="monospace")

    # warning-gap bracket, drawn below the road so it never crosses the building
    gap_y = 365
    ax.annotate("", xy=(SCENE["los"], gap_y), xytext=(SCENE["detect"], gap_y),
                arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.4))
    ax.text((SCENE["detect"] + SCENE["los"]) / 2, gap_y + 15, f"+{extra_time:.2f} s earlier warning",
            color=INK, fontsize=12.5, fontweight="bold", ha="center")

    ax.text(500, 415, "OTFS vs OFDM — 100 km/h, 28 GHz · Sionna, TDL-A channel, 9 dB SNR",
            color=INK_MUTED, ha="center", fontsize=10, family="monospace")

    # what the waveform actually sees: real per-cell error-rate grids
    ax_ofdm = fig.add_subplot(gs[1, 0])
    im = draw_error_grid(ax_ofdm, ofdm_grid, "OFDM — time–frequency grid",
                          "OFDM symbol (time) →", "↑ subcarrier (frequency)",
                          ofdm_ser, ACCENT, grid_vmax)

    ax_otfs = fig.add_subplot(gs[1, 1])
    draw_error_grid(ax_otfs, otfs_grid, "OTFS — delay–Doppler grid",
                     "delay bin →", "↑ Doppler bin",
                     otfs_ser, ACCENT_2, grid_vmax)

    cbar_ax = fig.add_axes([0.30, 0.045, 0.40, 0.012])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("per-cell symbol error rate", color=INK_MUTED, fontsize=9.5, family="monospace")
    cbar.ax.xaxis.set_major_formatter(lambda v, _: f"{v*100:.0f}%")
    cbar.ax.tick_params(colors=INK_MUTED, labelsize=8.5)
    cbar.outline.set_edgecolor(BORDER)

    fig.savefig("scenario_otfs_vs_ofdm.png", dpi=300, facecolor=BG, bbox_inches="tight")
    print("Saved scenario_otfs_vs_ofdm.png")
    plt.close(fig)


def fig_hybrid_ris():
    with open("../04_Sionna_SimuLltion_HYBRID_RIS/ris_beam_pattern.json") as f:
        rd = json.load(f)

    angles = np.deg2rad(rd["angles_deg"])
    idx0 = rd["active_fractions"].index(0.0)
    idx8 = rd["active_fractions"].index(0.08)
    pat0 = np.array(rd["patterns_db"][idx0])
    pat8 = np.array(rd["patterns_db"][idx8])

    # Standard antenna-pattern display convention: a fixed dynamic-range
    # window below peak (here 16 dB), not the full null-to-peak range --
    # the raw pattern has ~128 real sidelobes/nulls (physically correct for
    # a 128-element array) that are unreadable at full range in print.
    dbceil = max(pat0.max(), pat8.max()) + 1
    dbfloor = dbceil - 16
    r0 = np.clip((pat0 - dbfloor) / (dbceil - dbfloor), 0.0, 1.0)
    r8 = np.clip((pat8 - dbfloor) / (dbceil - dbfloor), 0.0, 1.0)

    fig = plt.figure(figsize=(9.5, 7.2), dpi=300)
    fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_facecolor(PANEL)

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetamin(-70)
    ax.set_thetamax(20)
    ax.set_ylim(0, 1.5)
    ax.set_yticklabels([])
    ax.grid(color=BORDER, alpha=0.6, linewidth=0.8)
    ax.spines["polar"].set_color(BORDER)
    for label in ax.get_xticklabels():
        label.set_color(INK_MUTED)
        label.set_fontsize(10)

    ax.fill(angles, r0, color=ACCENT, alpha=0.3, zorder=3)
    ax.plot(angles, r0, color=ACCENT, lw=4, alpha=0.9, solid_capstyle="round",
            zorder=4, label="Passive only (0% active)")

    ax.fill(angles, r8, color=ACCENT_2, alpha=0.4, zorder=5)
    ax.plot(angles, r8, color=ACCENT_2, lw=6, solid_capstyle="round",
            zorder=6, label="Hybrid — SENTRY (8% active)")

    target_rad = np.deg2rad(rd["theta_r_deg"])
    ax.plot([target_rad, target_rad], [0, 1.05], color=CRITICAL, lw=1.4, ls=(0, (4, 4)), zorder=7)
    ax.text(target_rad, 1.34, "HAZARD (−40°)", color=CRITICAL, ha="center", va="center",
            fontsize=11, fontweight="bold", family="monospace")

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.14), frameon=False,
              labelcolor=INK, fontsize=11.5, ncol=1)

    fig.text(0.5, 0.95, "HYBRID RIS — BEAM LOCK, LIVE", color=INK, ha="center",
              fontsize=17, fontweight="bold", family="monospace")
    fig.text(0.5, 0.905, "128-element RIS, 28 GHz · real array-factor pattern, not illustrative",
              color=INK_MUTED, ha="center", fontsize=10.5, family="monospace")

    g0 = rd["peak_gain_db"][idx0]
    g8 = rd["peak_gain_db"][idx8]
    fig.text(0.20, 0.06, f"Passive: {g0:.1f} dB\nbroad lobe, leaky sidelobes", color=ACCENT,
              ha="center", fontsize=11, family="monospace")
    fig.text(0.80, 0.06, f"Hybrid 8%: {g8:.1f} dB\n(+{g8-g0:.1f} dB) locked on target", color=ACCENT_2,
              ha="center", fontsize=11, fontweight="bold", family="monospace")

    fig.savefig("scenario_hybrid_ris.png", dpi=300, facecolor=BG, bbox_inches="tight")
    print("Saved scenario_hybrid_ris.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_otfs_vs_ofdm()
    fig_hybrid_ris()
