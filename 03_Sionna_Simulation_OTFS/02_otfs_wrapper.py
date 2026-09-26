"""
Step 2: Wrap Sionna's verified OFDM chain with an OTFS ISFFT/SFFT layer,
following the same fft(ifft(.)) construction as the team's own Simulation A,
and confirm the OTFS round trip is ALSO numerically exact with no channel.
"""
import torch
from sionna.phy.ofdm import ResourceGrid, ResourceGridMapper, ResourceGridDemapper, OFDMModulator, OFDMDemodulator
from sionna.phy.mapping import Mapper, Demapper, BinarySource

NUM_DELAY_BINS = 32        # fft_size / subcarriers
NUM_DOPPLER_BINS = 32      # num_ofdm_symbols
SUBCARRIER_SPACING = 15e3
CP_LEN = 8
NUM_BITS_PER_SYMBOL = 2    # QPSK

rg = ResourceGrid(
    num_ofdm_symbols=NUM_DOPPLER_BINS,
    fft_size=NUM_DELAY_BINS,
    subcarrier_spacing=SUBCARRIER_SPACING,
    cyclic_prefix_length=CP_LEN,
    num_tx=1, num_streams_per_tx=1,
)

def isfft(x_dd):
    """Delay-Doppler grid -> time-frequency grid.
    x_dd: [..., num_delay_bins, num_doppler_bins] (matches the team's own
    X_dd(delay, Doppler) convention from Simulation A)."""
    return torch.fft.fft(torch.fft.ifft(x_dd, dim=-1), dim=-2)

def sfft(x_tf):
    """Time-frequency grid -> delay-Doppler grid. Exact inverse of isfft
    (delay/Doppler axes are independent, so operations on each axis commute)."""
    return torch.fft.ifft(torch.fft.fft(x_tf, dim=-1), dim=-2)

# --- verify isfft/sfft really are exact inverses of each other, on their own ---
test = torch.randn(2, NUM_DELAY_BINS, NUM_DOPPLER_BINS, dtype=torch.complex64)
recon = sfft(isfft(test))
print("ISFFT/SFFT self-consistency max error:", torch.max(torch.abs(test - recon)).item())

# --- now the full OTFS chain: data -> ISFFT -> Sionna's resource grid mapper
#     -> Sionna's verified OFDM modulator -> (no channel yet) -> Sionna's
#     verified OFDM demodulator -> SFFT -> recovered delay-Doppler data ---
binary_source = BinarySource()
mapper = Mapper("qam", NUM_BITS_PER_SYMBOL)
demapper = Demapper("app", "qam", NUM_BITS_PER_SYMBOL)
rg_mapper = ResourceGridMapper(rg)
modulator = OFDMModulator(cyclic_prefix_length=CP_LEN)
demodulator = OFDMDemodulator(fft_size=NUM_DELAY_BINS, l_min=0, cyclic_prefix_length=CP_LEN)

batch_size = 4
num_data_symbols = rg.num_data_symbols
bits = binary_source([batch_size, 1, 1, num_data_symbols * NUM_BITS_PER_SYMBOL])
x_dd_flat = mapper(bits)                         # [batch,1,1,num_data_symbols] -- QPSK symbols in delay-Doppler "slots"

# Map the flat data-symbol stream onto the full (delay x Doppler) grid the
# same way ResourceGridMapper would for an ordinary OFDM payload -- then
# reinterpret that grid AS the delay-Doppler domain and run ISFFT on it.
x_dd_grid = rg_mapper(x_dd_flat)                  # [batch,1,1,num_doppler_bins,num_delay_bins]
x_tf_grid = isfft(x_dd_grid.transpose(-1, -2)).transpose(-1, -2)  # ISFFT expects (...,delay,doppler)

x_time = modulator(x_tf_grid)                     # Sionna's own verified IFFT + CP
y_tf_grid = demodulator(x_time)                   # Sionna's own verified CP removal + FFT (no channel yet)

y_dd_grid = sfft(y_tf_grid.transpose(-1, -2)).transpose(-1, -2)   # SFFT back to delay-Doppler

max_err = torch.max(torch.abs(x_dd_grid - y_dd_grid)).item()
print("Full OTFS round trip (ISFFT -> Sionna OFDM chain -> SFFT), no channel, max error:", max_err)
assert max_err < 1e-3, "OTFS round trip should be numerically exact with no channel"
print("\nPASS: OTFS-on-Sionna round trip is numerically exact with no channel.")
print("Next step: introduce a real Doppler/multipath channel between modulator and demodulator.")
