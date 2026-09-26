"""
Step 3: The result that actually matters for the POC.

Same SENTRY grid (32 delay bins x 32 Doppler bins, 15 kHz spacing, 28 GHz)
and the same verified Sionna OFDM chain and OTFS wrapper from steps 1-2 --
now with a REAL 3GPP TDL-A (NLOS) channel at a real vehicle speed between
the modulator and demodulator, instead of no channel at all.

Compares: does the OTFS (ISFFT/SFFT) path recover data more reliably than
reading the same corrupted signal directly in the OFDM domain?

--- SCOPE NOTE, established here deliberately ---
This does NOT mean SENTRY replaces OFDM everywhere. OTFS is used ONLY on
the roadside sensing link (RSU -> RIS -> reflected echo), because that is
specifically the high-Doppler, NLOS link. The alert a vehicle actually
receives still travels over standard, unmodified C-V2X (Uu + PC5), which
stays OFDM-based -- exactly as documented in the Ground Truth doc's V2X
Protocols section: "a vehicle only needs a conventional V2X receiver to
benefit from SENTRY; OTFS stays entirely on the infrastructure side."
This script is testing that infrastructure-side link only.
"""
import torch
from sionna.phy.ofdm import ResourceGrid, ResourceGridMapper, OFDMModulator, OFDMDemodulator
from sionna.phy.mapping import Mapper, BinarySource
from sionna.phy.channel.tr38901 import TDL
from sionna.phy.channel import GenerateTimeChannel, ApplyTimeChannel, time_lag_discrete_time_channel

# ---------------- SENTRY's exact parameters ----------------
NUM_DELAY_BINS = 32
NUM_DOPPLER_BINS = 32
SUBCARRIER_SPACING = 15e3
CP_LEN = 8
CARRIER_FREQ = 28e9
NUM_BITS_PER_SYMBOL = 2          # QPSK
SPEED_KMH = 100.0
SPEED_MS = SPEED_KMH / 3.6
DELAY_SPREAD = 30e-9             # dense urban NLOS, seconds
BATCH_SIZE = 200                 # Monte Carlo trials

rg = ResourceGrid(
    num_ofdm_symbols=NUM_DOPPLER_BINS, fft_size=NUM_DELAY_BINS,
    subcarrier_spacing=SUBCARRIER_SPACING, cyclic_prefix_length=CP_LEN,
    num_tx=1, num_streams_per_tx=1,
)
bandwidth = rg.bandwidth
l_min, l_max = time_lag_discrete_time_channel(bandwidth=bandwidth)
l_tot = l_max - l_min + 1
print(f"bandwidth={bandwidth} Hz, l_min={l_min}, l_max={l_max}, l_tot={l_tot}")

# ---------------- channel: real 3GPP TDL-A (NLOS), real Doppler from real speed ----------------
tdl = TDL(model="A", delay_spread=DELAY_SPREAD, carrier_frequency=CARRIER_FREQ,
          min_speed=SPEED_MS, max_speed=SPEED_MS)
fd = SPEED_MS * CARRIER_FREQ / 3e8
print(f"Vehicle speed: {SPEED_KMH} km/h -> Doppler fd = {fd:.1f} Hz "
      f"({100*fd/SUBCARRIER_SPACING:.1f}% of {SUBCARRIER_SPACING/1e3:.0f} kHz subcarrier spacing)")

# ---------------- building blocks ----------------
binary_source = BinarySource()
mapper = Mapper("qam", NUM_BITS_PER_SYMBOL)
rg_mapper = ResourceGridMapper(rg)
modulator = OFDMModulator(cyclic_prefix_length=CP_LEN)
demodulator = OFDMDemodulator(fft_size=NUM_DELAY_BINS, l_min=l_min, cyclic_prefix_length=CP_LEN)

def isfft(x):
    return torch.fft.fft(torch.fft.ifft(x, dim=-1), dim=-2)

def sfft(x):
    return torch.fft.ifft(torch.fft.fft(x, dim=-1), dim=-2)

def qpsk_ser(tx_syms, rx_syms):
    """Nearest-constellation-point symbol error rate for QPSK."""
    tx_bits = torch.stack([tx_syms.real > 0, tx_syms.imag > 0], dim=-1)
    rx_bits = torch.stack([rx_syms.real > 0, rx_syms.imag > 0], dim=-1)
    sym_err = (tx_bits != rx_bits).any(dim=-1)
    return sym_err.float().mean().item()

def run_trial(otfs: bool, snr_db: float):
    bits = binary_source([BATCH_SIZE, 1, 1, rg.num_data_symbols * NUM_BITS_PER_SYMBOL])
    x_syms = mapper(bits)                                  # flat QPSK stream, the ground truth to compare against
    x_grid = rg_mapper(x_syms)                              # [B,1,1,num_doppler,num_delay]

    if otfs:
        x_tf = isfft(x_grid.transpose(-1, -2)).transpose(-1, -2)
    else:
        x_tf = x_grid

    x_time = modulator(x_tf)                                # [B,1,1,num_time_samples]
    num_time_samples = x_time.shape[-1]

    gen_time_channel = GenerateTimeChannel(
        channel_model=tdl, bandwidth=bandwidth,
        num_time_samples=num_time_samples, l_min=l_min, l_max=l_max,
    )
    apply_time_channel = ApplyTimeChannel(num_time_samples=num_time_samples, l_tot=l_tot)

    h_time = gen_time_channel(BATCH_SIZE)                   # real TDL-A taps at this speed/Doppler
    no = 10 ** (-snr_db / 10)                                # noise power per complex dim, signal power ~1
    y_time = apply_time_channel(x_time, h_time, no)          # channel + AWGN in one step

    y_tf = demodulator(y_time)                               # Sionna's own verified CP-removal + FFT

    if otfs:
        y_grid = sfft(y_tf.transpose(-1, -2)).transpose(-1, -2)
    else:
        y_grid = y_tf

    # read the recovered symbols back off the grid the same way they were placed
    y_syms = y_grid.reshape(x_syms.shape[0], x_syms.shape[1], x_syms.shape[2], -1)[..., :x_syms.shape[-1]]
    return qpsk_ser(x_syms, y_syms)

print("\nSNR (dB) | OFDM SER | OTFS SER")
for snr_db in [0, 5, 10, 13, 15, 20]:
    ofdm_ser = run_trial(otfs=False, snr_db=snr_db)
    otfs_ser = run_trial(otfs=True, snr_db=snr_db)
    print(f"{snr_db:8.0f} | {ofdm_ser:8.4f} | {otfs_ser:8.4f}")
