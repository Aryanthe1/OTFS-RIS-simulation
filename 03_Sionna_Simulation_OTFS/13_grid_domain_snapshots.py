"""
Step 7: produce the actual 2D grid data behind "the OFDM time-frequency
grid vs the OTFS delay-Doppler grid" story, instead of only a scalar
SER number per (speed, SNR) as in script 09.

Same method as 05/09 exactly (Sionna, TDL-A, 32x32 grid at SENTRY's
28 GHz / 15 kHz numerology, scalar MMSE equalization with perfect CSI)
-- the only change is that run_trial now returns a per-grid-cell error
PROBABILITY (fraction of the batch wrong at that cell), not a single
mean. That per-cell grid is exactly what a live dashboard can render as
a heatmap and have it be real, not illustrative:

  - OFDM: grid axes are (OFDM symbol index = time, subcarrier index =
    frequency) -- the demodulated grid is never SFFT'd back, so this
    *is* the time-frequency grid.
  - OTFS: grid axes are (Doppler bin, delay bin) -- the grid mapped
    onto the resource grid before ISFFT (== the grid recovered by SFFT
    at the receiver) is, by construction, the delay-Doppler domain.

Fixed SNR = 9 dB for every speed: script 05's single-speed sweep showed
0-3 dB is noise-dominated (both waveforms tie) and OTFS's real edge
opens up from ~9 dB. Holding SNR fixed isolates what changes with
speed/Doppler alone -- exactly the demo point ("same channel quality,
different vehicle speed").
"""
import time
import json
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
BATCH_SIZE = 400
FIXED_SNR_DB = 9.0
C = 3e8

SPEEDS_KMH = [20, 60, 100, 140, 180]

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


def error_grid(tx_grid, rx_grid):
    """Per-cell QPSK error probability, averaged over the batch.
    tx_grid/rx_grid: [B,1,1,NUM_DOPPLER_BINS,NUM_DELAY_BINS] complex."""
    tx_bits = torch.stack([tx_grid.real > 0, tx_grid.imag > 0], dim=-1)
    rx_bits = torch.stack([rx_grid.real > 0, rx_grid.imag > 0], dim=-1)
    wrong = (tx_bits != rx_bits).any(dim=-1).float()   # [B,1,1,32,32]
    return wrong.mean(dim=0).squeeze(0).squeeze(0)      # [32,32]


def run_trial(otfs: bool, snr_db: float, tdl: TDL):
    bits = binary_source([BATCH_SIZE, 1, 1, rg.num_data_symbols * NUM_BITS_PER_SYMBOL])
    x_syms = mapper(bits)
    x_grid = rg_mapper(x_syms)                              # [B,1,1,32,32], DD-domain if otfs
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
    grid = error_grid(x_grid, y_grid)
    return grid, grid.mean().item()


results = {
    "speeds_kmh": SPEEDS_KMH,
    "snr_db": FIXED_SNR_DB,
    "num_doppler_bins": NUM_DOPPLER_BINS,
    "num_delay_bins": NUM_DELAY_BINS,
    "ofdm_axes": ["ofdm_symbol_time_index", "subcarrier_freq_index"],
    "otfs_axes": ["doppler_bin_index", "delay_bin_index"],
    "ofdm_error_grid": [],   # [speed] -> 32x32
    "otfs_error_grid": [],   # [speed] -> 32x32
    "ofdm_ser": [],
    "otfs_ser": [],
}

t_start = time.time()
with torch.no_grad():
    for speed_kmh in SPEEDS_KMH:
        speed_ms = speed_kmh / 3.6
        fd = speed_ms * CARRIER_FREQ / C
        doppler_pct = 100 * fd / SUBCARRIER_SPACING

        tdl = TDL(model="A", delay_spread=DELAY_SPREAD, carrier_frequency=CARRIER_FREQ,
                  min_speed=speed_ms, max_speed=speed_ms)

        ofdm_grid, ofdm_ser = run_trial(otfs=False, snr_db=FIXED_SNR_DB, tdl=tdl)
        otfs_grid, otfs_ser = run_trial(otfs=True, snr_db=FIXED_SNR_DB, tdl=tdl)

        results["ofdm_error_grid"].append([[round(v, 4) for v in row] for row in ofdm_grid.tolist()])
        results["otfs_error_grid"].append([[round(v, 4) for v in row] for row in otfs_grid.tolist()])
        results["ofdm_ser"].append(round(ofdm_ser, 4))
        results["otfs_ser"].append(round(otfs_ser, 4))

        print(f"{speed_kmh:4d} km/h (fd={fd:7.1f} Hz, {doppler_pct:5.1f}% of Df) @ {FIXED_SNR_DB} dB | "
              f"OFDM SER {ofdm_ser:.4f} | OTFS SER {otfs_ser:.4f}")

print(f"\nElapsed: {time.time() - t_start:.1f}s")

with open("grid_domain_snapshots.json", "w") as f:
    json.dump(results, f)
print("Saved results to grid_domain_snapshots.json")
