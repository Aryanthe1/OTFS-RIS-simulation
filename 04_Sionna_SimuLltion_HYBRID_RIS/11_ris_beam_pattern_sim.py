"""
Extends script 06's array physics (same N=128, 28 GHz, half-wavelength
linear RIS, theta_i=30deg incidence / theta_r=-40deg NLOS target, 1-bit
passive quantization + full-phase active elements) from a single scalar
gain number into a full angular radiation pattern -- i.e. the actual
beamforming shape the panel produces, not just its peak value.

The RIS's per-element phase is fixed (computed once, to cancel the
propagation gradient AT theta_r). Sweeping the OBSERVATION angle and
recomputing the array factor at each one is exactly how a phased-array /
RIS radiation pattern is normally characterized -- it's what shows WHY a
given active fraction produces a tighter beam and lower sidelobes, not
just what its peak gain is. This is the "coherent sense" version of
script 06's line chart: the schematic + polar pattern in script 12 reads
directly off this file's angle sweep.

One concrete active-element layout is drawn per active fraction (fixed
seed 0, same generator as script 06's Monte Carlo) rather than averaged
across trials -- a radiation pattern is a property of one physical panel,
not an ensemble statistic. Script 06's Monte Carlo mean gain is the
number that belongs in prose; this file's peak-at-theta_r gain for the
same seed is consistent with it (matches within Monte Carlo std).
"""
import torch
import numpy as np
import json

N = 128
FREQ = 28e9
C = 3e8
WAVELENGTH = C / FREQ
D = WAVELENGTH / 2
ACTIVE_GAIN_DB = 12.0

THETA_I = np.deg2rad(30)
THETA_R = np.deg2rad(-40)

ACTIVE_FRACTIONS = [0.0, 0.08, 0.30]   # pure passive | SENTRY's hybrid sweet spot | heavy-active
QUANT_BITS = 1

n_idx = torch.arange(N, dtype=torch.float64)
natural_phase_at_target = (2 * np.pi / WAVELENGTH) * D * n_idx * (np.sin(THETA_I) + np.sin(THETA_R))
desired_ris_phase = torch.remainder(-natural_phase_at_target, 2 * np.pi)

levels = 2 ** QUANT_BITS
step = 2 * np.pi / levels
quantized_ris_phase = torch.round(desired_ris_phase / step) * step

gen = torch.Generator().manual_seed(0)


def active_mask_for(fraction):
    num_active = int(round(fraction * N))
    mask = torch.zeros(N, dtype=torch.bool)
    if num_active > 0:
        idx = torch.randperm(N, generator=gen)[:num_active]
        mask[idx] = True
    return mask


def array_factor_db(active_mask, theta_obs_rad):
    """Radiation pattern: recompute the propagation phase at each
    observation angle, keep the panel's fixed applied phase, sum."""
    ris_phase_applied = torch.where(active_mask, desired_ris_phase, quantized_ris_phase)
    amp = torch.where(active_mask, torch.tensor(10 ** (ACTIVE_GAIN_DB / 20), dtype=torch.float64),
                       torch.tensor(1.0, dtype=torch.float64))

    theta = torch.as_tensor(theta_obs_rad, dtype=torch.float64)
    # [num_angles, N]
    natural_phase = (2 * np.pi / WAVELENGTH) * D * n_idx[None, :] * \
        (np.sin(THETA_I) + torch.sin(theta)[:, None])
    total_phase = natural_phase + ris_phase_applied[None, :]
    contrib = amp[None, :] * torch.complex(torch.cos(total_phase), torch.sin(total_phase))
    combined = contrib.sum(dim=-1)
    power = combined.abs() ** 2
    return (10 * torch.log10(power)).numpy()


angles_deg = np.linspace(-90, 90, 721)
angles_rad = np.deg2rad(angles_deg)

results = {"angles_deg": angles_deg.tolist(), "theta_i_deg": 30.0, "theta_r_deg": -40.0,
           "active_fractions": ACTIVE_FRACTIONS, "patterns_db": [], "active_masks": [],
           "peak_gain_db": []}

for frac in ACTIVE_FRACTIONS:
    mask = active_mask_for(frac)
    pattern_db = array_factor_db(mask, angles_rad)
    results["patterns_db"].append(pattern_db.tolist())
    results["active_masks"].append(mask.tolist())
    peak = float(pattern_db.max())
    results["peak_gain_db"].append(peak)
    print(f"Active fraction {frac*100:5.1f}% | peak gain {peak:6.2f} dB at "
          f"{angles_deg[pattern_db.argmax()]:6.1f} deg (target {np.rad2deg(THETA_R):.0f} deg)")

with open("ris_beam_pattern.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved results to ris_beam_pattern.json")
