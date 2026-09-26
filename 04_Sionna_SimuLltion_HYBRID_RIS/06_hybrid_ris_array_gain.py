"""
Hybrid RIS array-gain simulation: SENTRY's actual N=128 configuration,
Monte Carlo over which elements are active vs passive and real per-element
phase quantization -- not a closed-form estimate borrowed from someone
else's element count.

NOTE ON TOOLING: this does NOT use sionna.rt. Sionna RT's dedicated `RIS`
scene class existed in the old TensorFlow-based Sionna (v0.18) but does not
appear to have been ported to the current, installable PyTorch-based
sionna-rt 2.x line (checked: no RIS-related class in `dir(sionna.rt)`, and
none of the sionna-rt v1.2.0-v2.0.1 release notes mention RIS). Building
this directly on the array physics is the honest, buildable alternative --
it's also literally the math that produces SENTRY's cited 42.1 dB / 3.9 dB
numbers, so this simulation reproduces AND extends those, rather than just
re-citing them.

Model: a 128-element linear RIS, half-wavelength spacing, at 28 GHz.
A subset of elements are "active" (real amplifier gain, full phase
resolution); the rest are passive (1-bit phase quantization, i.e. 0 or pi
only -- the cheapest, most deployable option, per Wu & Zhang). Computes
coherent-combining array gain vs the fraction of elements that are active.
"""
import torch
import numpy as np

N = 128
FREQ = 28e9
C = 3e8
WAVELENGTH = C / FREQ
D = WAVELENGTH / 2          # standard half-wavelength element spacing
ACTIVE_GAIN_DB = 12.0        # per-element amplifier gain for active elements

THETA_I = np.deg2rad(30)     # incidence angle from the RSU
THETA_R = np.deg2rad(-40)    # reflection angle toward the NLOS target

n_idx = torch.arange(N, dtype=torch.float64)
# natural propagation phase difference across elements (physics, not RIS-controlled)
natural_phase = (2 * np.pi / WAVELENGTH) * D * n_idx * (np.sin(THETA_I) + np.sin(THETA_R))
# the RIS-applied phase needed at each element to CANCEL that natural gradient,
# so every element's total (natural + applied) phase lines up at the target
desired_ris_phase = torch.remainder(-natural_phase, 2 * np.pi)

def array_gain_db(active_fraction: float, quant_bits: int = 1, n_trials: int = 3000, seed: int = 0):
    """Monte Carlo over which specific elements are active (random subset,
    since panel wiring/placement of the active subset isn't fixed a priori)."""
    gen = torch.Generator().manual_seed(seed)
    num_active = int(round(active_fraction * N))
    levels = 2 ** quant_bits
    step = 2 * np.pi / levels
    quantized_ris_phase = torch.round(desired_ris_phase / step) * step

    gains_db = torch.empty(n_trials)
    for t in range(n_trials):
        active_mask = torch.zeros(N, dtype=torch.bool)
        if num_active > 0:
            idx = torch.randperm(N, generator=gen)[:num_active]
            active_mask[idx] = True

        # active elements get the exact (continuous) compensating phase;
        # passive elements only get the nearest 1-bit-quantized approximation
        ris_phase_applied = torch.where(active_mask, desired_ris_phase, quantized_ris_phase)
        total_phase = natural_phase + ris_phase_applied   # what actually arrives at the target

        amp = torch.where(active_mask, torch.tensor(10 ** (ACTIVE_GAIN_DB / 20), dtype=torch.float64),
                           torch.tensor(1.0, dtype=torch.float64))

        contrib = amp * torch.complex(torch.cos(total_phase), torch.sin(total_phase))
        combined = contrib.sum()
        power = combined.abs() ** 2
        gains_db[t] = 10 * torch.log10(power)

    return gains_db.mean().item(), gains_db.std().item()

# ---- sanity checks against the closed-form numbers already in the docs ----
ideal_gain_db = 20 * np.log10(N)
print(f"Ideal coherent gain (N={N}, continuous phase, all passive-equivalent, no loss): "
      f"20*log10(N) = {ideal_gain_db:.2f} dB  (docs cite 42.1 dB)")

pure_passive_mean, pure_passive_std = array_gain_db(active_fraction=0.0)
print(f"Simulated pure-passive, 1-bit quantized (0% active): {pure_passive_mean:.2f} dB "
      f"(std {pure_passive_std:.2f}) -- quantization loss vs ideal: {ideal_gain_db - pure_passive_mean:.2f} dB "
      f"(docs cite ~3.9 dB from Wu & Zhang)")

print("\nActive fraction | Array gain (dB) | Gain over pure-passive baseline (dB)")
fractions = [0.0, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0]
results = {"fraction": [], "gain_db": [], "gain_std": [], "gain_over_passive_db": []}
for f in fractions:
    mean_db, std_db = array_gain_db(active_fraction=f)
    over_passive = mean_db - pure_passive_mean
    print(f"{f*100:14.0f}% | {mean_db:15.2f} | {over_passive:8.2f}")
    results["fraction"].append(f)
    results["gain_db"].append(mean_db)
    results["gain_std"].append(std_db)
    results["gain_over_passive_db"].append(over_passive)

import json
with open("hybrid_ris_results.json", "w") as fp:
    json.dump(results, fp, indent=2)
print("\nSaved results to hybrid_ris_results.json")
