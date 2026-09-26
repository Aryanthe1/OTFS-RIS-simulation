import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

with open("lmmse_results.json") as f:
    r = json.load(f)

snr = r["snr_db"]
ofdm = [v*100 for v in r["ofdm_ser"]]
otfs = [v*100 for v in r["otfs_ser"]]

fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=220)

ax.plot(snr, ofdm, marker='o', ms=6, lw=2.4, color="#D85A30", label="OFDM")
ax.plot(snr, otfs, marker='o', ms=6, lw=2.4, color="#0F6E56", label="OTFS")

ax.set_xlabel("SNR (dB)", fontsize=12.5)
ax.set_ylabel("Symbol Error Rate (%)", fontsize=12.5)
ax.set_title("OTFS vs OFDM under a Real 3GPP TDL-A Channel\n100 km/h @ 28 GHz \u2014 Simulated in Sionna (NVIDIA)",
             fontsize=13, fontweight="bold", color="#1F3864", pad=12)

ax.grid(True, alpha=0.25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(fontsize=12, frameon=False, loc="upper right")

# highlight the operating region where OTFS's advantage is clearest
ax.axvspan(9, 18, color="#0F6E56", alpha=0.06)
ax.text(13.5, max(ofdm)*0.95, "OTFS advantage", ha="center", fontsize=9.5,
        color="#0F6E56", style="italic")

plt.tight_layout()
plt.savefig("otfs_vs_ofdm_sionna.png", dpi=220, facecolor="white")
print("saved")
