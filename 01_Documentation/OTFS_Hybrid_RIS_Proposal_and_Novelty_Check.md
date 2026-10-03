# The Proposal, Stated Precisely — and a Novelty Check

> **Note on how this was produced:** A live web search was run this turn (after an
> initial transient tool outage cleared) specifically to check current prior art
> before writing the verdict below. The citations in Section 3 are real, verified
> papers — titles, authors, dates and venues were confirmed directly, not taken on
> a search engine's summary alone. This is a targeted spot-check, not a formal
> search, so it does not replace the **formal CPC-classified patent/freedom-to-operate
> search** this project's own v3 proposal already names as a prerequisite before any
> public novelty claim, and which had not been done as of the last recorded session.
> Treat the findings below as reason to take that formal search seriously and soon —
> not as a substitute for it.

## 1. What is actually being proposed

Stripped down to the physical-layer architecture, independent of the specific
"blind intersection" application, the proposal is:

**1. Start from a standard OFDM link.** Ordinary OFDM numerology — in this
project's case, 28 GHz carrier, 15 kHz subcarrier spacing, a 32×32
time-symbol × subcarrier resource grid.

**2. Overlay OTFS on top of that OFDM link, not replace it.** Data symbols are
mapped onto a *delay-Doppler* grid rather than directly onto the OFDM
time-frequency grid. Before transmission, an Inverse Symplectic Finite Fourier
Transform (ISFFT) converts that delay-Doppler grid into the same
time-frequency grid an OFDM modulator already expects, so the actual radio
transmit/receive chain is unmodified OFDM hardware. At the receiver, a
Symplectic Finite Fourier Transform (SFFT) converts the demodulated
time-frequency grid back into the delay-Doppler domain for detection. No new
modulator is invented — OTFS is added as a pre/post-processing wrapper around
an existing OFDM chain.

**3. Scope the OTFS overlay to one link only.** In this project's design, OTFS
is used *only* on the roadside sensing link (roadside unit → RIS → reflected
echo back). The link that actually delivers a hazard alert to a vehicle stays
on plain, unmodified OFDM-based C-V2X — no vehicle needs an OTFS receiver.

**4. Add a 128-element hybrid RIS to handle non-line-of-sight (NLOS) geometry.**
A linear reflecting array of 128 elements at 28 GHz, half-wavelength element
spacing, predominantly passive (1-bit phase-quantized reflection) with a
small active-element minority (this project targets ~8%) added for gain
recovery. This hybrid mix is a deliberate middle point between a fully
passive RIS (weaker, but needs no extra power) and a fully active RIS
(stronger, but defeats the "no second powered sensor" design premise this
project is built around).

**5. Use the RIS to bend the OTFS signal around an obstruction.** The RIS's
job is purely geometric: physically redirect the roadside unit's OTFS-encoded
signal around a building or similar obstruction so it can reach — and receive
a reflection back from — a target that has no direct line of sight to the
roadside unit.

**6. Read the returned signal as both communication and sensing at once.**
Because OTFS represents data natively in the delay-Doppler domain — which is
also exactly the representation a radar needs (delay → range, Doppler →
radial velocity) — the same received signal that would normally just be
demodulated for data can also be read for range/velocity information about
whatever it reflected off. That is the "integrated sensing and communication"
(ISAC) part: one signal, two uses, no separate radar transmitter.

## 2. Is this novel? — checked piece by piece, against real, verified sources

| Component | Is it novel on its own? | Verified prior art |
|---|---|---|
| OTFS built as an ISFFT/SFFT wrapper around an OFDM chain | **No** | Standard OTFS construction since Hadani et al.'s original work; this project's own Sionna implementation uses the same method. |
| RIS for NLOS coverage/redirection | **No** | One of the most heavily published 6G PHY topics of the last several years. |
| RIS combined specifically with OTFS, including hybrid (passive+active) RIS at mmWave | **No** | A whole survey paper exists on exactly this sub-field: *"A survey on reconfigurable intelligent surface-assisted orthogonal time frequency space systems"* (TU Berlin). More pointedly, *"Joint Channel Estimation and Data Detection for Hybrid RIS aided Millimeter Wave OTFS Systems"* ([arXiv:2208.06781](https://arxiv.org/abs/2208.06781)) combines **hybrid RIS + OTFS + mmWave** — the same three technical ingredients this project's PHY layer uses — in a 2022 paper. |
| OTFS-ISAC specifically at a roadside unit, for vehicle sensing + communication together | **No — this is direct, on-point prior art** | *"Integrated Sensing and Communication-Assisted Orthogonal Time Frequency Space Transmission for Vehicular Networks,"* Weijie Yuan, Zhiqiang Wei, Shuangyang Li, Jinhong Yuan, Derrick Wing Kwan Ng, **IEEE Journal on Selected Topics in Signal Processing, Nov 2021**. Verified abstract: *"the roadside unit (RSU) is capable of simultaneously transmitting downlink information to the vehicles and estimating the sensing parameters of vehicles"* — i.e., exactly this project's "one OTFS signal, two uses, from an RSU" mechanism, published in 2021. It does **not** mention blind intersections, pedestrians, or RIS. |
| RIS bending sensing *around a corner* specifically to detect a pedestrian, for an automotive look-ahead warning use case | **No — very close, very recent prior art** | *"Around-the-corner Radar Sensing Using Reconfigurable Intelligent Surface,"* Kainat Yasmeen, Debidas Kundu, Shobha Sundar Ram, **arXiv, Feb 12 2026** ([2602.11471](https://arxiv.org/abs/2602.11471)). Verified abstract: RIS strengthens NLOS multipath so that "micro-Doppler signatures of the walking motion of humans can now be captured in NLOS conditions," explicitly framed for "automotive scenarios" and "look-ahead warning systems." Confirmed **not** to use OTFS, and not framed around a roadside-infrastructure/V2X/intersection deployment — but the core physical mechanism (RIS bends sensing around an obstruction to see a pedestrian, for automotive early warning) is the same idea, published seven months before this check. |
| The *problem statement* itself — guaranteeing sensing coverage for NLOS areas at road crossroads | **Already on a 3GPP standards body's radar** | A ZTE contribution titled *"Guaranteed sensing for NLOS area at crossroads,"* submitted to 3GPP TSG-SA WG1 Meeting #99e, **August 2022**. Confirms the crossroads-NLOS-sensing problem statement was already being raised inside 3GPP standardization discussions years before this project. |
| **The full integration**: hybrid-RIS-redirected **OTFS specifically**, read as ISAC, deployed at a blind road intersection, designed to avoid a second powered sensor | **Not found as a single combined system** | Every adjacent piece above is published; no single found source combines OTFS (rather than an unspecified/FMCW-style radar waveform) with RIS-redirected around-corner sensing in a roadside V2X deployment. This is the sliver that's left. |

## 3. The honest verdict — narrower than a first pass suggests

The live search **does not just fail to help the novelty claim — it actively narrows it further.**
Before this check, this project's own prior documentation described novelty as
resting on "no one has integrated all these pieces." That's still technically
true, but the pieces now confirmed to already exist are more specific and
closer to this project's exact design than that framing implies:

- The core ISAC mechanism — one OTFS signal from an RSU doing double duty as
  communication and vehicle sensing — **was already published in 2021**, not
  just "OTFS exists" and "ISAC exists" separately.
- The core sensing mechanism — a RIS bending a signal around a corner
  specifically to detect a pedestrian's micro-Doppler signature, for an
  automotive look-ahead warning — **was already published in February 2026**,
  seven months before this check, at 5.5 GHz with real experimental results.
- The problem statement — guaranteed NLOS sensing coverage at crossroads —
  **was already raised inside 3GPP** in 2022.

What survives is a genuinely narrow, specific gap: nobody found in this check
has published the combination of *OTFS specifically* (not a generic radar
waveform) with *RIS-redirected around-corner sensing* in a *roadside V2X
deployment* aimed at *blind-intersection safety*. That is a real, defensible,
but thin claim — closer to "we combined a 2021 mechanism with a February-2026
mechanism in a way nobody has published yet" than to "we invented a new
sensing paradigm." Any of the three research groups whose papers turned up
here could plausibly extend their own work to close this exact gap.

This changes the practical recommendation: the February 2026 "around-the-corner
radar" paper in particular should be read in full and directly cited and
distinguished from in this project's own documentation — not just noted as an
adjacent finding — because it is close enough that a judge or reviewer who has
seen it will ask "how is this different?" and the project needs a specific,
prepared answer (most likely: OTFS's native delay-Doppler representation and
its dual use on the communication side, versus that paper's apparent
radar-only framing — but this should be confirmed by reading the full paper,
not assumed from the abstract).

## 4. What would make the novelty claim stronger

1. **Read the February 2026 "around-the-corner radar" paper in full** ([arXiv:2602.11471](https://arxiv.org/abs/2602.11471)) and the 2021 OTFS-ISAC-RSU paper in full, not just their abstracts. This check confirmed they exist and are close; it did not read their full methods sections. Know exactly what they do and do not claim before presenting anywhere a judge might have also read them.
2. **Run the formal prior-art/patent search** (CPC classes covering OTFS,
   RIS/IRS, ISAC, and roadside V2X safety systems) that has been flagged as
   outstanding since the v3 proposal — now more urgent given how close the
   Feb 2026 paper is. Until this happens, the novelty claim is a research
   team's belief, not a verified position.
3. **Lead with the application, not the PHY technique**, in any pitch,
   poster, or paper framing — "roadside ISAC for blind-corner safety without
   a second powered sensor" is the actual claim; "OTFS + RIS" alone is not,
   and is now confirmed to already exist in combination (hybrid RIS + OTFS +
   mmWave, 2022).
4. **Name the gap explicitly and narrowly**: *"no published system combines
   OTFS specifically — not a generic radar waveform — with RIS-redirected
   around-corner sensing in a roadside V2X deployment for blind-intersection
   safety"* is the precise, defensible sentence this check supports. Broader
   claims ("novel use of OTFS and RIS," "first to combine sensing and RIS for
   safety") are not defensible after this search and will not survive contact
   with a judge who has seen the same papers.
5. **Have the obviousness rebuttal ready, specifically against the Feb 2026 paper.**
   The most likely judge question is now "how is this different from the
   around-the-corner radar paper?" — have a specific, technical answer (OTFS's
   dual comm+sensing use via the delay-Doppler domain, versus that paper's
   apparent radar-only framing), confirmed by actually reading it, not assumed.
