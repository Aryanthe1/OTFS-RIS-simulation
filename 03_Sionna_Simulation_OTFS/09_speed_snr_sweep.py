"""
Step 6: extend script 05's single-speed LMMSE comparison into a full
speed x SNR sweep. Same method exactly (Sionna, TDL-A, 32x32 grid at
SENTRY's 28 GHz / 15 kHz numerology, scalar MMSE equalization with
perfect CSI) -- only the sweep dimensionality changes, from one line
(SER vs SNR at 100 km/h) to a 2D grid (SER vs SNR vs speed), so the
result can be rendered as a heatmap instead of a single curve.

Speed grid brackets SENTRY's actual 100 km/h operating point on both
sides (20-200 km/h -> ~3.5%-34.6% of subcarrier spacing in fractional
Doppler terms), so the heatmap shows not just "OTFS wins at 100 km/h"
but the full operating envelope: where the two waveforms tie, where
OTFS's advantage opens up, and where it eventually closes again.

--- SCOPE NOTE (same as script 05) ---
OTFS is used ONLY on the roadside sensing link (RSU -> RIS -> reflected
echo) -- the high-Doppler, NLOS link. The vehicle-facing alert stays on
standard C-V2X (OFDM-based). This script tests the infrastructure-side
link only.
"""
import time
import torch
from sionna.phy.ofdm import ResourceGrid, ResourceGridMapper, OFDMModulator, OFDMDemodulator
from sionna.phy.mapping import Mapper, BinarySource
from sionna.phy.channel.tr38901 import TDL
from sionna.phy.channel import (
    ApplyTimeChannel, time_lag_discrete_time_channel,
    cir_to_time_channel, cir_to_ofdm_channel, subcarrier_frequencies,
)

NUM_DELAY_BINS = 32
NUM_DOPPLER_BINS = 32
SUBCARRIER_SPACING = 15e3
CP_LEN = 8
CARRIER_FREQ = 28e9
NUM_BITS_PER_SYMBOL = 2
DELAY_SPREAD = 30e-9
BATCH_SIZE = 250
C = 3e8

SPEEDS_KMH = [20, 40, 60, 80, 100, 130, 160, 200]
SNR_DB_LIST = [0, 3, 6, 9, 12, 15, 18, 21]

rg = ResourceGrid(
    num_ofdm_symbols=NUM_DOPPLER_BINS, fft_size=NUM_DELAY_BINS,
    subcarrier_spacing=SUBCARRIER_SPACING, cyclic_prefix_length=CP_LEN,
    num_tx=1, num_streams_per_tx=1,
)
bandwidth = rg.bandwidth
l_min, l_max = time_lag_discrete_time_channel(bandwidth=bandwidth)
l_tot = l_max - l_min + 1

binary_source = BinarySource()
mapper = Mapper("qam", NUM_BITS_PER_SYMBOL)
rg_mapper = ResourceGridMapper(rg)
modulator = OFDMModulator(cyclic_prefix_length=CP_LEN)
demodulator = OFDMDemodulator(fft_size=NUM_DELAY_BINS, l_min=l_min, cyclic_prefix_length=CP_LEN)
frequencies = subcarrier_frequencies(NUM_DELAY_BINS, SUBCARRIER_SPACING)


def isfft(x):
    return torch.fft.fft(torch.fft.ifft(x, dim=-1), dim=-2)


def sfft(x):
    return torch.fft.ifft(torch.fft.fft(x, dim=-1), dim=-2)


def qpsk_ser(tx_syms, rx_syms):
    tx_bits = torch.stack([tx_syms.real > 0, tx_syms.imag > 0], dim=-1)
    rx_bits = torch.stack([rx_syms.real > 0, rx_syms.imag > 0], dim=-1)
    return (tx_bits != rx_bits).any(dim=-1).float().mean().item()


def run_trial(otfs: bool, snr_db: float, tdl: TDL):
    bits = binary_source([BATCH_SIZE, 1, 1, rg.num_data_symbols * NUM_BITS_PER_SYMBOL])
    x_syms = mapper(bits)
    x_grid = rg_mapper(x_syms)
    x_tf = isfft(x_grid.transpose(-1, -2)).transpose(-1, -2) if otfs else x_grid

    x_time = modulator(x_tf)
    num_time_samples = x_time.shape[-1]

    a, tau = tdl(BATCH_SIZE, num_time_samples + l_tot - 1, bandwidth)
    h_time = cir_to_time_channel(bandwidth, a, tau, l_min, l_max)

    apply_channel = ApplyTimeChannel(num_time_samples=num_time_samples, l_tot=l_tot)
    no = 10 ** (-snr_db / 10)
    y_time = apply_channel(x_time, h_time, no)

    y_tf = demodulator(y_time)

    h_freq_full = cir_to_ofdm_channel(frequencies, a, tau)
    num_cir_steps = h_freq_full.shape[-2]
    step = num_cir_steps // NUM_DOPPLER_BINS
    h_freq = h_freq_full[..., step // 2::step, :][..., :NUM_DOPPLER_BINS, :]
    h_freq = h_freq.squeeze(4).squeeze(3)

    y_tf_eq = (torch.conj(h_freq) / (h_freq.abs() ** 2 + no)) * y_tf

    y_grid = sfft(y_tf_eq.transpose(-1, -2)).transpose(-1, -2) if otfs else y_tf_eq
    y_syms = y_grid.reshape(x_syms.shape[0], x_syms.shape[1], x_syms.shape[2], -1)[..., :x_syms.shape[-1]]
    return qpsk_ser(x_syms, y_syms)


results = {
    "speeds_kmh": SPEEDS_KMH,
    "snr_db": SNR_DB_LIST,
    "doppler_fraction_pct": [],
    "ofdm_ser": [],   # [speed][snr]
    "otfs_ser": [],   # [speed][snr]
}

t_start = time.time()
with torch.no_grad():
    for speed_kmh in SPEEDS_KMH:
        speed_ms = speed_kmh / 3.6
        fd = speed_ms * CARRIER_FREQ / C
        doppler_pct = 100 * fd / SUBCARRIER_SPACING
        results["doppler_fraction_pct"].append(doppler_pct)

        tdl = TDL(model="A", delay_spread=DELAY_SPREAD, carrier_frequency=CARRIER_FREQ,
                  min_speed=speed_ms, max_speed=speed_ms)

        ofdm_row, otfs_row = [], []
        for snr_db in SNR_DB_LIST:
            ofdm_row.append(run_trial(otfs=False, snr_db=snr_db, tdl=tdl))
            otfs_row.append(run_trial(otfs=True, snr_db=snr_db, tdl=tdl))
        results["ofdm_ser"].append(ofdm_row)
        results["otfs_ser"].append(otfs_row)

        print(f"{speed_kmh:4d} km/h (fd={fd:7.1f} Hz, {doppler_pct:5.1f}% of Df) | "
              f"OFDM {['%.3f' % v for v in ofdm_row]} | OTFS {['%.3f' % v for v in otfs_row]}")

print(f"\nElapsed: {time.time() - t_start:.1f}s")

import json
with open("speed_snr_sweep.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved results to speed_snr_sweep.json")
