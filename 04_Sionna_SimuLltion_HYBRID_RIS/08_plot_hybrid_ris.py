import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

with open("hybrid_ris_results.json") as f:
    r = json.load(f)

frac = [f*100 for f in r["fraction"]]
gain = r["gain_db"]
over_passive = r["gain_over_passive_db"]
N = 128

# marginal gain per active element (efficiency proxy) -- skip fraction=0 (div by zero)
eff_frac, eff_val = [], []
for f, g in zip(r["fraction"], over_passive):
    if f > 0:
        num_active = round(f * N)
        eff_frac.append(f * 100)
        eff_val.append(g / num_active)

fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), dpi=220)

ax = axes[0]
ax.plot(frac, gain, marker='o', ms=6, lw=2.4, color="#0F6E56")
ax.axhline(42.14, color="#8a8a8a", linestyle="--", linewidth=1.2, label="Ideal (continuous phase, all elements)")
ax.axhline(gain[0], color="#D85A30", linestyle=":", linewidth=1.4, label="Pure passive, 1-bit (0% active)")
ax.set_xlabel("Active elements (% of 128)", fontsize=11.5)
ax.set_ylabel("Array gain (dB)", fontsize=11.5)
ax.set_title("Hybrid RIS: Array Gain vs. Active Fraction", fontsize=12.5, fontweight="bold", color="#1F3864")
ax.grid(True, alpha=0.25)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.legend(fontsize=9, frameon=False, loc="lower right")
ax.axvspan(5, 10, color="#0F6E56", alpha=0.08)

ax2 = axes[1]
ax2.plot(eff_frac, eff_val, marker='o', ms=6, lw=2.4, color="#185FA5")
ax2.set_xlabel("Active elements (% of 128)", fontsize=11.5)
ax2.set_ylabel("Marginal gain per active element (dB)", fontsize=11.5)
ax2.set_title("Efficiency: Diminishing Returns per\nAdditional Active Element", fontsize=12.5, fontweight="bold", color="#1F3864")
ax2.grid(True, alpha=0.25)
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
ax2.axvspan(5, 10, color="#0F6E56", alpha=0.08)

fig.suptitle("SENTRY's 128-Element Hybrid RIS \u2014 Simulated (28 GHz, 1-bit passive + full-phase active)",
             fontsize=12, color="#595959", y=1.02)
plt.tight_layout()
plt.savefig("hybrid_ris_gain.png", dpi=220, facecolor="white", bbox_inches="tight")
print("saved")
