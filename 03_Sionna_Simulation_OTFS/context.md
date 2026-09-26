# SENTRY — Conversation Context & Handoff

Purpose: paste this into a new Claude conversation (any machine) to resume work on SENTRY without re-deriving anything already established below. Written as of the end of an extended working session; treat everything here as settled unless the person says otherwise.

## What SENTRY is

A roadside 6G ISAC (Integrated Sensing and Communication) hardware system, built by a student team, that lets a vehicle detect a hazard (pedestrian, cyclist, cross-traffic) it has no line of sight to at a blind, obstructed intersection. Core mechanism: one OTFS-encoded signal from a roadside unit (RSU) does double duty — it's both the communication link and, via its reflection off a hazard, a radar-style sensing return — redirected around the obstruction by a passive Reconfigurable Intelligent Surface (RIS). The pitch is architectural: this avoids installing a second, independently powered sensor at every blind corner in a city.

Originally written for the Vishwakarma Awards 2026–27 (Theme 7). Now being repositioned for **India Mobile Congress (IMC) 2026** (7–10 Oct, New Delhi, theme "Scale without Boundaries").

## Team — Team CacheMe

- **Aryan Iyengar** — Physical Layer & Waveform (OTFS vs. OFDM, Doppler analysis, Simulation A). This is the person I've mostly been working with in this conversation.
- **Mou** — Electromagnetics & Spatial Link Budget (RIS physics, link budget, Simulation B).
- **Om Goyal** — Edge AI & System Execution (micro-Doppler classification, TTC, latency budget, O-RAN RIC, Simulation C).

## Version history: v1 → v2 → v3

- **v1** (original Stage 1 Application, Vishwakarma framing): purely passive RIS (ideal, lossless, always-coherent); RSU already carried sensing-side compute; clean synthetic channel with no clutter modeled; single network path assumed for alert delivery.
- **v2**: four hardening additions, each answering a specific v1 idealization — Active-Reflection RIS (passive by default, active boost under degraded conditions), RSU-side pre-coding (offloads known/static channel geometry upstream, lightens vehicle compute), Zero-Doppler masking + spatio-temporal AI (handles real clutter), Dual-Path Broadcast (cellular + sidelink redundancy for the alert).
- **v3**: five corrections/additions driven by a structured research pass (not just internal suggestion) — corrected the v1→v2 table's mischaracterization of where compute originally lived; corrected an unsupported claim that OTFS is "a candidate waveform in next-gen standards discussions" (it isn't — ISAC as a category is standards-recognized, OTFS itself is not); added a validation roadmap (Section 6.1: BER-vs-SNR target, fractional-Doppler test, bandwidth/range-resolution gap); added a cost-parity defense against "just use conventional radar" (Section 6.2, real USDOT cost benchmarks); reordered the patent roadmap so a formal FTO search precedes any filing, not follows it. **Most recent addition (this session): Section 6.3, justifying the active/passive/hybrid RIS choice with real citations** — see "Latest decision" below.

## Established facts — do not re-derive, cite directly

- Carrier frequency 28 GHz; 15 kHz subcarrier spacing (SENTRY's default numerology).
- Doppler shift formula: fd = (v/c) × fc. At 100 km/h and 28 GHz, fd ≈ 2.59 kHz (~17% of 15 kHz spacing).
- **Important nuance surfaced this session**: the "is OFDM fine at high speed" question depends on fc, not just v. 500 km/h at 3.6 GHz (3GPP's own high-speed-rail spec, Release 16) produces only ~1.67 kHz Doppler — less than SENTRY's own 100 km/h at 28 GHz. Verified via a real Monte Carlo simulation (not illustrative) — see "Simulations run" below.
- RIS: 128 elements; modeled blockage penalty ~+45 dB; ideal coherent gain 20·log₁₀(128) ≈ 42.1 dB; 1-bit phase quantization penalty ≈ 3.9 dB (Wu & Zhang).
- Active-Reflection RIS (v2/v3): now specified as passive-by-default with a **~5–10% active element fraction** (added this session, sourced from hybrid-RIS energy-efficiency literature — see below).
- Analytical sense-to-act latency budget: 8.7 ms across 5 stages (Sense 1.5, Detect 3.2, Decide 1.0, Communicate 0.5, Act 2.5) — explicitly flagged as analytical, not hardware-profiled.
- TTC alert threshold: 1.5 s (Hayward 1972's classical surrogate-safety threshold — SENTRY's number matches the literature almost exactly, a good talking point).
- India context: MoRTH *Road Accidents in India 2024* — 84,599 two-wheeler deaths, 25,769 pedestrian deaths (these are the *current, verified* figures; earlier team drafts used older/unverified numbers like "~13,000 black spots" and "74,897/9,000" — those were flagged as needing refresh and should not be reused without re-checking).

## Documents that exist and where

**Two live Claude Docs** (persistent, cross-session, cross-machine — open directly):
1. **"SENTRY — Deep Research Brief for ChatGPT"** — `https://claude.ai/code/artifact/77575c22-f4fd-4d1f-a205-76bce2bf0ef1`
   Main tab: the research brief (project summary, established facts, literature, known gaps, 8 prioritized research questions, output format spec) — written to hand to ChatGPT's deep-research mode.
   Second tab, **"Understanding Log & Why-Chain"**: a log of the ground-level Q&A that built up OFDM/OTFS understanding, plus a dedicated 5-whys interrogation of the OFDM→OTFS switch itself (distinct from the mechanism-level why-chain in the research assessment below).
2. **"SENTRY Ground Truth — How the System Works, Component by Component"** — `https://claude.ai/code/artifact/ce294654-57de-4475-aff1-723312707a77`
   Full technical reference: OFDM (incl. building-blocks diagram, the corrected 200 km/h analysis with a real simulated chart + data table), OTFS (incl. building-blocks diagram, the honest fractional-Doppler simulation finding, the Sionna validation-path writeup), V2X protocols (DSRC/802.11p, C-V2X PC5+Uu, and the key clarification that **vehicles need only standard V2X receivers, not OTFS receivers** — OTFS stays entirely roadside-side), ISAC standards & O-RAN, RIS (incl. the hybrid active/passive trade-off with citations), Edge AI/sensing pipeline, full pipeline walkthrough, glossary. This is the single best "read this to understand the whole system" document.

**An Advanced Research report** (ran via the research/launch_extended_search_task tool, rendered as an artifact titled *"SENTRY: Prior Art, Feasibility, and IMC 2026 Positioning for RIS plus OTFS Blind-Intersection Safety"*): covers patent/novelty risk (no single patent claims the full RIS+OTFS+roadside-ISAC combination, but every component is separately prior art — novelty is an integration claim, exposed to an obviousness challenge), competitive landscape (Derq, Autotalks/Yunex, USDOT cost benchmarks $9k–$142.5k/intersection; no operator has piloted RIS+OTFS specifically), standards currency (3GPP Release 19/20 sensing is OFDM-based and UAV-first; ISAC confirmed as a Release 21 theme), India regulatory (28 GHz needs WPC-licensed spectrum, not de-licensed — a real hurdle), funding pathways (DoT DCIS, NIDHI-PRAYAS, IIT Madras/Hyderabad), technical benchmarks (OTFS ~13 dB SNR @ 10⁻³ BER in comparable literature; edge inference latency benchmarks), and a synthesis of the 3 toughest judge questions with prepared rebuttals. *(This was rendered as a standalone artifact, not one of the two Claude Docs above — if it isn't in the new session's context, it may need to be re-run or the person may have a separate link to it.)*

**Word doc deliverables** (built via a Node/docx.js script pattern, verified by converting to PDF and visually inspecting before delivery each time):
- `SENTRY_Aryan_IMC_Documentation.docx` — individual physical-layer contribution report for IMC.
- `SENTRY_Full_Project_IMC_Documentation.docx` — full three-pillar team documentation for IMC.
- `SENTRY_v3_Proposal.docx` — the hardened v3 proposal (highlighted-diff style like the team's own v2 doc), including Section 6.3 on the active/passive/hybrid RIS decision.
- `SENTRY Ground Truth — How the System Works, Component by Component.docx` — a full Word export of the Ground Truth Claude Doc (12 pages, images included). Note it goes stale if the live doc is edited further; re-export via the doc's export function for a fresh copy.

**The IMC poster** — `SENTRY_IMC_Poster.pptx`. Built by taking a real SRM ECE-department poster template (uploaded by the user, originally a different team's "Sign Language Translation" poster) and swapping every section for SENTRY content, keeping the authentic SRM/CeNCRA header branding. Key details worth knowing if it's edited further:
- The two image slots (portrait-oriented) hold custom-built "Before SENTRY / After SENTRY" blind-intersection panels, not photos — recreated from the original Stage 1 application's Section 8 diagram concept.
- Terminology precision matters here and was fixed multiple times: **"Hybrid RIS"**, not "Active RIS" (the latter specifically means the fully-active alternative SENTRY's own docs argue against — mixing them up contradicts the project's own reasoning). Exact protocol names used throughout: **C-V2X (Uu + PC5)**, **O-RAN Near-RT RIC**, **Active-Reflection RIS** (the full term, used where space allows).
- Hardware/software requirements line reflects the team's *actual* tooling: **Sionna** (not MATLAB), and **college MEC server** (not a Jetson board) for edge AI.
- All text boxes use PowerPoint's shape-autofits-to-text behavior — longer text pushes into the box below. Any future edits need a visual re-check (convert to PDF, inspect) before trusting it, exactly as done throughout this build.

**These deliverables are chat-delivered downloads, not guaranteed to exist on a new machine/session** — only the two Claude Docs (links above) are reliably cross-session. If the person needs a Word file or the poster again, regenerate it (the build patterns are documented in this file's process notes, and the actual build scripts may still be in the sandbox's `/home/claude` if the session hasn't reset).

## Simulations actually run this session (real, not illustrative)

Building the OFDM-vs-OTFS comparison hit real complexity worth knowing about before attempting it again:
- A clean, **verified** single-symbol OFDM intra-symbol ICI simulation (Monte Carlo, real AWGN, hand-rolled numpy) produced the SER-vs-speed chart now in both the Ground Truth doc and this session's chat — confirms OFDM is fine at cellular frequencies to 500 km/h, breaks down by ~150 km/h at 28 GHz.
- Multiple attempts at a matching **from-scratch OTFS simulation** (also numpy) hit a genuine, non-bug phenomenon: fractional (off-grid) Doppler bins cause real leakage — performance swings from near-perfect to near-random depending on whether the true Doppler lands on vs. between discrete grid bins. Not a simulation error — a first-hand demonstration of the "fractional delay-Doppler" gap already flagged as unresolved.

### Sionna build (this session, real infrastructure — see `sionna_sim/` folder)

Moved off hand-rolled numpy onto **Sionna** (NVIDIA's link-level PHY simulator) to get a credible, tool-backed version of the OTFS-vs-OFDM comparison. Five scripts, built and debugged incrementally, each verified before moving to the next:

1. `01_resource_grid_sanity.py` — SENTRY's exact grid (32×32, 15 kHz) as a real Sionna `ResourceGrid`. Confirmed bandwidth = 480 kHz and, a number not previously in the docs, **OFDM symbol duration = 83.33 µs including an 8-sample cyclic prefix** (the 66.7 µs figure used everywhere else is CP-free). Clean round trip, error ~3×10⁻⁷.
2. `02_otfs_wrapper.py` — the ISFFT/SFFT wrapper (same `fft(ifft(·))` construction as the team's own Simulation A) built around Sionna's own OFDM modulator/demodulator. Clean round trip, error ~6×10⁻⁷.
3. `03_doppler_comparison.py` — first attempt at adding a real channel (3GPP TDL-A). Result: both OFDM and OTFS stuck at ~75% SER (= random guessing for QPSK) — diagnosed as **missing equalization entirely**, not a Doppler finding. A real multipath channel multiplies the signal by an unknown gain; without correcting for it, decisions fail regardless of Doppler.
4. `04_equalized_comparison.py` — added zero-forcing (ZF) equalization with perfect channel knowledge. Both curves now behave sensibly (error falls with SNR) — but **OFDM beat OTFS at every SNR**. Real, repeatable, and explainable: ZF amplifies noise at channel fades; OFDM keeps that damage localized to one symbol, but OTFS's ISFFT/SFFT spreads every delay-Doppler value across the whole grid, so a few bad fades corrupt *every* recovered OTFS symbol via the SFFT sum. This is exactly why the validation roadmap named **LMMSE, not ZF** — the distinction turned out to matter concretely, not just as phrasing.
5. `05_lmmse_comparison.py` — swapped in the scalar/SISO MMSE equalizer (mathematically identical to `sionna.phy.ofdm.LMMSEEqualizer` for a single stream, without its full MIMO `StreamManagement` overhead). **Result: OTFS and OFDM tie at low SNR (0–3 dB, noise-dominated), OTFS clearly wins 9–18 dB (its real advantage), and narrows again at 21 dB** (MMSE converges toward ZF-like behavior as noise power → 0, where OTFS's weakness re-emerges). Real, at SENTRY's actual 100 km/h / 28 GHz operating point, 3GPP TDL-A channel, batch=150 for stability. Saved as `lmmse_results.json` and plotted in `otfs_vs_ofdm_sionna.png`.

**Environment notes if re-running this:** Sionna 2.x splits into `sionna` (link-level, PyTorch-based) and `sionna-rt` (ray tracing, Mitsuba/Dr.Jit-based, GPU-oriented). The sandbox this was built in has no GPU and started with only ~3 GB disk — the full `pip install sionna` blew past that pulling CUDA packages. Fix: `pip install torch --no-deps` (554 MB, CPU-only) then `pip install sionna --no-deps` — `sionna.phy` works fine on CPU with no GPU needed. `sionna.rt` (needed for the RIS ray-tracing half, not yet attempted) is heavier and untested in this environment — size it up before assuming it fits. Also: this sandbox has only ~3.9 GB RAM; batch sizes above ~150–200 for this grid size triggered OOM kills even with `torch.no_grad()` — not a bug, just a hard resource ceiling here specifically.

**Not yet done:** larger, more statistically powered sweep; multiple speeds (only 100 km/h tested); the RIS ray-tracing half (`sionna.rt`) entirely untested in this environment; a version of this result written up for the docs (currently only in chat + the standalone plot).

## House style / design discipline running through this whole project

- **Honesty about gaps is treated as a feature, not a weakness** — every claim distinguishes measured/simulated/modeled vs. analytical/unvalidated, explicitly. Don't paper over this when producing new content.
- **Real citations only.** Multiple rounds of this conversation involved verifying claims against actual literature (3GPP specs, IEEE papers, arXiv) rather than accepting team assertions at face value — including catching an unsupported claim in v2 and correcting it in v3.
- **A recurring "5-whys, simulate a skeptical industry specialist" technique** has been used to stress-test claims — drilling until the justification bottoms out at a named, defensible premise (or reveals one that's contestable). Worth reusing this technique if asked to interrogate a new claim.
- **Judge-question prep is a running thread** — the v3 doc and Ground Truth doc both exist partly to make sure the team has prepared, sourced answers to the questions a technical judge would actually ask, rather than leaving them for live improvisation.
- **When using an unfamiliar library/API, read the actual source before guessing signatures.** The Sionna build lost real time to guessed method signatures that were wrong (`OFDMModulator(rg)` vs. the actual `OFDMModulator(cyclic_prefix_length=...)`; assuming `__call__` when the real method was `.call`; a shape bug from an unnecessary manual reshape where `cir_to_time_channel` already returned the right shape). Every one of these was resolved fastest by reading `inspect.signature(...)` or the source file directly, not by trial and error.

## Latest decisions

**Hybrid RIS** (in the v3 doc and now the poster): heavily passive-weighted, with a concrete ~5–10% active-element target. Grounded in: passive RIS suffers *multiplicative* path loss vs. active RIS's *additive* loss + amplification gain (~40 dB better SNR in one cited comparison); but Zhi et al. (IEEE Comm. Letters, 2022) found active RIS only wins under a fixed power budget unless that budget is very small or element count very large — and SENTRY's founding "no second powered unit" constraint puts it deliberately in the small-budget regime; hybrid architectures matching SENTRY's exact pattern are published (a 2023 "HAPR" paper), and a 2024 paper found most of the energy-efficiency benefit comes from a *minority* of active elements (as few as 8%). Forward-looking, not-yet-built idea also flagged: hybrid RIS's active elements could in principle do local angle-of-arrival sensing at the panel itself — named as future work.

**The Sionna OTFS-vs-OFDM result** (see above): real, not yet added to any doc or the poster — currently exists only as the standalone plot and chat discussion. A placement decision is still open (see below).

## Open threads / plausible next asks

- Formal CPC-classified patent/FTO search (named as a prerequisite before any public novelty claim, not yet done).
- **Partially addressed this session**: a real BER-vs-SNR-style curve for OTFS vs OFDM now exists (Sionna, MMSE-equalized, real TDL-A channel) — but only at one speed (100 km/h), one channel model (TDL-A), and modest statistical power (batch=150). Broadening this is the natural next step, not starting from scratch.
- Whether/how to get the new Sionna plot onto the poster — no free slot currently exists (both image slots are full with the Before/After panels); decision was left open rather than forced.
- `sionna.rt` (RIS ray tracing) entirely unattempted in this environment — disk/GPU feasibility here specifically is still unknown.
- Hardware profiling of the 8.7 ms latency budget — now should target the **college MEC server** specifically (per this session's poster correction), not a generic Jetson board as earlier literature comparisons assumed.
- SENTRY's own installed per-intersection cost is still unquantified (flagged explicitly in v3 Section 6.2 as a named gap, not yet closed).
- IMC 2026 submission logistics (ASPIRE track, TCOE deadline ~20 Aug 2026 per one source — flagged as needing confirmation on the official portal).
