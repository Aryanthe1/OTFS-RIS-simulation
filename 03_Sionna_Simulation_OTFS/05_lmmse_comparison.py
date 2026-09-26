"""
Step 4: same setup as script 04, but with MMSE equalization instead of
perfect-CSI zero-forcing equalization. Step 3's first attempt showed both
stuck at ~0.75 SER (= random guessing for QPSK) because a real multipath
channel multiplies the signal by an unknown gain -- without correcting for
that, decisions fail regardless of Doppler. This is the standard genie-aided
baseline (equalize using known channel state) that isolates the Doppler
question cleanly, before adding the separate complexity of imperfect,
pilot-based channel estimation.

--- SCOPE NOTE, established here deliberately ---
OTFS is used ONLY on the roadside sensing link (RSU -> RIS -> reflected
echo) -- the high-Doppler, NLOS link. The alert a vehicle actually receives
still travels over standard, unmodified C-V2X (Uu + PC5), which stays
OFDM-based. This script tests the infrastructure-side link only.
"""
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
SPEED_KMH = 100.0
SPEED_MS = SPEED_KMH / 3.6
DELAY_SPREAD = 30e-9
BATCH_SIZE = 150

rg = ResourceGrid(
    num_ofdm_symbols=NUM_DOPPLER_BINS, fft_size=NUM_DELAY_BINS,
    subcarrier_spacing=SUBCARRIER_SPACING, cyclic_prefix_length=CP_LEN,
    num_tx=1, num_streams_per_tx=1,
)
bandwidth = rg.bandwidth
l_min, l_max = time_lag_discrete_time_channel(bandwidth=bandwidth)
l_tot = l_max - l_min + 1

tdl = TDL(model="A", delay_spread=DELAY_SPREAD, carrier_frequency=CARRIER_FREQ,
          min_speed=SPEED_MS, max_speed=SPEED_MS)
fd = SPEED_MS * CARRIER_FREQ / 3e8
print(f"Vehicle speed: {SPEED_KMH} km/h -> Doppler fd = {fd:.1f} Hz "
      f"({100*fd/SUBCARRIER_SPACING:.1f}% of subcarrier spacing)")

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

def run_trial(otfs: bool, snr_db: float):
    bits = binary_source([BATCH_SIZE, 1, 1, rg.num_data_symbols * NUM_BITS_PER_SYMBOL])
    x_syms = mapper(bits)
    x_grid = rg_mapper(x_syms)                              # [B,1,1,num_doppler,num_delay]
    x_tf = isfft(x_grid.transpose(-1, -2)).transpose(-1, -2) if otfs else x_grid

    x_time = modulator(x_tf)
    num_time_samples = x_time.shape[-1]

    # ONE shared channel realization, used to derive BOTH the time-domain
    # taps (for the physical channel) and the frequency-domain response
    # (for equalization) -- avoids any risk of the two representations
    # drifting out of sync.
    a, tau = tdl(BATCH_SIZE, num_time_samples + l_tot - 1, bandwidth)
    h_time = cir_to_time_channel(bandwidth, a, tau, l_min, l_max)   # already the exact shape ApplyTimeChannel wants

    apply_channel = ApplyTimeChannel(num_time_samples=num_time_samples, l_tot=l_tot)
    no = 10 ** (-snr_db / 10)
    y_time = apply_channel(x_time, h_time, no)

    y_tf = demodulator(y_time)                               # [B,1,1,num_doppler,num_delay]

    # Perfect-CSI zero-forcing equalization in the time-frequency domain.
    # h_freq_full: [batch,1,1,1,1,num_time_steps(1294),fft_size(32)] -- the
    # time axis is at position -2 (NOT -1, that's frequency/subcarrier);
    # downsample it to one representative sample per OFDM symbol (32 of them).
    h_freq_full = cir_to_ofdm_channel(frequencies, a, tau)
    num_cir_steps = h_freq_full.shape[-2]
    step = num_cir_steps // NUM_DOPPLER_BINS
    h_freq = h_freq_full[..., step // 2::step, :][..., :NUM_DOPPLER_BINS, :]  # [...,32,32]
    h_freq = h_freq.squeeze(4).squeeze(3)              # drop singleton num_tx, num_tx_ant

    # MMSE equalization (the scalar/SISO reduction of LMMSE -- mathematically
    # identical to sionna.phy.ofdm.LMMSEEqualizer for a single tx/rx stream,
    # without needing its full MIMO StreamManagement setup). This is the
    # equalizer the validation roadmap actually names -- zero-forcing
    # (plain division) amplifies noise at channel fades, which spreads
    # across every OTFS symbol via the SFFT; MMSE trades a little bias for
    # much better noise control, exactly where OTFS needs it.
    y_tf_eq = (torch.conj(h_freq) / (h_freq.abs()**2 + no)) * y_tf

    y_grid = sfft(y_tf_eq.transpose(-1, -2)).transpose(-1, -2) if otfs else y_tf_eq
    y_syms = y_grid.reshape(x_syms.shape[0], x_syms.shape[1], x_syms.shape[2], -1)[..., :x_syms.shape[-1]]
    return qpsk_ser(x_syms, y_syms)

print("\nSNR (dB) | OFDM SER | OTFS SER")
results = {"snr_db": [], "ofdm_ser": [], "otfs_ser": []}
with torch.no_grad():
    for snr_db in [0, 3, 6, 9, 12, 15, 18, 21]:
        ofdm_ser = run_trial(otfs=False, snr_db=snr_db)
        otfs_ser = run_trial(otfs=True, snr_db=snr_db)
        results["snr_db"].append(snr_db)
        results["ofdm_ser"].append(ofdm_ser)
        results["otfs_ser"].append(otfs_ser)
        print(f"{snr_db:8.0f} | {ofdm_ser:8.4f} | {otfs_ser:8.4f}")

import json
with open("lmmse_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved results to lmmse_results.json")
