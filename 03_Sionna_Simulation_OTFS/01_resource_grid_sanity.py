"""
Step 1: Set up SENTRY's own grid parameters as a Sionna ResourceGrid,
and verify a clean (no-channel) round trip reproduces the input exactly.
This is the sanity check everything else builds on.
"""
import torch
from sionna.phy.ofdm import ResourceGrid, ResourceGridMapper, OFDMModulator, OFDMDemodulator, ResourceGridDemapper
from sionna.phy.mapping import Mapper, Demapper, BinarySource

# --- SENTRY's exact parameters (Simulation A / Ground Truth doc) ---
NUM_SUBCARRIERS = 32      # delay bins
NUM_OFDM_SYMBOLS = 32     # Doppler bins / symbols per frame
SUBCARRIER_SPACING = 15e3 # Hz
CYCLIC_PREFIX_LEN = 8     # samples (1/4 of FFT size, a standard NR-like ratio)
CARRIER_FREQ = 28e9       # Hz, SENTRY's operating band

rg = ResourceGrid(
    num_ofdm_symbols=NUM_OFDM_SYMBOLS,
    fft_size=NUM_SUBCARRIERS,
    subcarrier_spacing=SUBCARRIER_SPACING,
    cyclic_prefix_length=CYCLIC_PREFIX_LEN,
    num_tx=1,
    num_streams_per_tx=1,
)
print("ResourceGrid built OK")
print("  num_ofdm_symbols:", rg.num_ofdm_symbols)
print("  fft_size:", rg.fft_size)
print("  subcarrier_spacing:", rg.subcarrier_spacing)
print("  cyclic_prefix_length:", rg.cyclic_prefix_length)
print("  bandwidth (Hz):", rg.bandwidth)
print("  ofdm_symbol_duration (s):", rg.ofdm_symbol_duration)

# --- Round-trip sanity: random QAM symbols -> grid -> time domain -> back -> recover exactly ---
NUM_BITS_PER_SYMBOL = 2  # QPSK
batch_size = 4

binary_source = BinarySource()
mapper = Mapper("qam", NUM_BITS_PER_SYMBOL)
rg_mapper = ResourceGridMapper(rg)
modulator = OFDMModulator(cyclic_prefix_length=CYCLIC_PREFIX_LEN)
demodulator = OFDMDemodulator(fft_size=NUM_SUBCARRIERS, l_min=0, cyclic_prefix_length=CYCLIC_PREFIX_LEN)

num_data_symbols = rg.num_data_symbols
bits = binary_source([batch_size, 1, 1, num_data_symbols * NUM_BITS_PER_SYMBOL])
x_qam = mapper(bits)                          # [batch, 1, 1, num_data_symbols]
x_rg = rg_mapper(x_qam)                        # mapped onto the full resource grid
x_time = modulator(x_rg)                       # OFDM-modulated time-domain signal (IFFT + CP)
print("\nTime-domain signal shape:", x_time.shape)

y_rg = demodulator(x_time)                     # OFDM-demodulated back to resource grid (remove CP + FFT)
max_err = torch.max(torch.abs(x_rg - y_rg)).item()
print("Max |error| after modulate -> demodulate round trip (no channel):", max_err)
assert max_err < 1e-4, "Round trip should be numerically exact with no channel"
print("\nPASS: clean round trip is numerically exact.")
