# Mentor Prep — CNN-GRU-Attention vs ImgFi

Everything you need to defend [Action_NoAction_CNN_GRU.ipynb](Action_NoAction_CNN_GRU.ipynb),
with every number measured from our own data. Study Parts 1–5; Part 8 is the rapid-fire bank.

**Golden rule for the whole meeting:** every claim you make should be backed by a cell in the
notebook you can scroll to. If you cannot point at it, do not claim it.

---

## Part 0 — The 60-second opening

> "We captured 8 CSI takes on a USRP N210 — two people, `action` vs `noaction`, 322 windows
> of 2 seconds. We built two pipelines. The first follows ImgFi: turn each of the 52
> subcarriers into a recurrence-plot image and classify all 52 with a ResNet-18, then majority
> vote. The second is ours: feed the whole 52×200 amplitude matrix to a CNN-GRU with attention
> in a single pass.
>
> Ours gets 98.4% cross-subject with 0.57 million parameters instead of 11.2 million, and one
> forward pass instead of 52. But the honest headline is this: **a single scalar feature with
> one threshold also gets 98.4%.** So this binary task does not prove our architecture is
> better — it proves the capture-to-evaluation chain works. I can show you exactly why we
> still believe the architecture is the right choice for the 7-class problem, and I measured
> the three things that justify it."

That framing does two things: it gets ahead of the "your accuracy is meaningless" objection,
and it shows you know the difference between *validating a pipeline* and *validating a model*.

---

## Part 1 — CSI fundamentals (she will start here)

### What is CSI, physically?

When a WiFi transmitter sends an OFDM frame, the receiver estimates the channel from the
known preamble. For each subcarrier *k* it recovers a complex number:

$$H_k = \text{Re}_k + j\,\text{Im}_k$$

$|H_k|$ is how much that frequency was attenuated; $\angle H_k$ is how much it was delayed.
A person moving between transmitter and receiver changes the multipath environment, so
$H_k$ changes over time. **That time-variation is the entire sensing signal.**

### Why exactly 52 subcarriers?

802.11a/g at 20 MHz uses a 64-point FFT → 64 subcarrier slots. Of these, 12 are unused
(DC null + guard bands at the edges), leaving **52 usable subcarriers** (48 data + 4 pilot).
This is dictated by the standard — **we did not choose 52**, it is what the PHY gives us.

- Intel 5300 NIC datasets (UT-HAR, Widar 3.0, SignFi) report only **30** subcarriers because
  the NIC firmware reports a subsampled subset.
- **We report all 52** — finer frequency resolution than the Intel-based datasets.
- ARIL (also USRP-based) also has 52. Our front-end matches theirs.

> **If asked "why not 64?"** → 12 are null by standard (DC + guards); there is no channel
> estimate to report for them.

### Why amplitude only? Why throw away phase?

**This is the most likely first hard question. Full answer:**

Our USRP is *not* synchronised to the MacBook. Three independent offsets corrupt the phase
of every packet:

| Offset | Cause | Effect on phase |
|---|---|---|
| **CFO** (carrier frequency offset) | TX and RX local oscillators differ | rotation growing over the packet |
| **SFO** (sampling frequency offset) | ADC clocks differ | subcarrier-dependent linear ramp |
| **PBD / timing offset** | packet detection lands a few samples off | linear ramp across subcarriers |

These change **randomly packet to packet**, so the raw phase is effectively noise. Amplitude
$|H| = \sqrt{\text{Re}^2 + \text{Im}^2}$ is invariant to all three (they are pure phase
rotations).

**Two strong supporting arguments:**

1. **ARIL discards phase too** — and they had *two* USRPs with an OctoClock GPS-disciplined
   clock and controlled both ends. If a fully synchronised setup still drops phase, our
   passive-sniffing setup certainly should.
2. **Widar 3.0 uses phase, but only phase *differences between antennas* on the same NIC.**
   The offsets are common to all antennas on one card, so subtracting cancels them. **That
   trick needs ≥2 receive antennas. We have one (SISO), so it is impossible for us in
   principle** — not merely unimplemented.

> **If she says "phase carries more information, papers use it"** → agree, then explain the
> antenna-difference requirement above. Then say: *"adding a second RX antenna is on our
> upgrade list precisely because it unlocks phase-difference features like Widar's DFS/BVP."*
> That turns a weakness into a roadmap item.

### What does one sample look like?

- One row of the CSV = one decoded 802.11 frame = `Packet, Timestamp_us, SC0_Re, SC0_Im, … SC51_Re, SC51_Im` (106 columns).
- We capture at **51.5–77.6 Hz** (mean **66.4 Hz**) — this is *packets per second*, i.e. our sampling rate.
- One training sample = **2 seconds = 52 subcarriers × 200 time steps**.

---

## Part 2 — Data pipeline, step by step (§1–§5 of the notebook)

| Step | What happens | Why |
|---|---|---|
| 1. Capture | USRP passively sniffs MacBook→hotspot frames; `extract_csi` filters by MAC and writes CSV | Passive = no control over rate; realistic deployment scenario |
| 2. Amplitude | $\lvert H\rvert=\text{hypot}(\text{Re},\text{Im})$ | Phase unusable (Part 1) |
| 3. Windowing | 2 s spans, **resampled onto a uniform grid using real timestamps** → exactly 52×200 | Packets arrive irregularly (median gap 12 ms, worst 464 ms). Interpolating onto a time grid makes every window exactly 2 s of wall clock |
| 4. Fill check | Skip window if <50% of expected packets | Prevents mostly-interpolated windows entering the dataset |
| 5. Detrend | Subtract each subcarrier's temporal mean | Removes the large static component (room geometry, gain, distance) which carries no motion info; also gives robustness to slow gain drift |
| 6. Scale | Divide by per-subcarrier std **from the training split only** | Subcarriers have different baseline variance (frequency-selective fading). Training-only avoids leakage |

### Numbers to have memorised

- **322 windows** total: 168 `action`, 154 `noaction` (52.2% action — balanced).
- By subject: amrith **182**, rishiikesh **140**.
- By take: walk 87, mixed 81, stand 81, sit 73.
- Each capture has **exactly 1 truncated final row** (Ctrl+C landed mid-write) — we drop it explicitly. 0.015% of data. Cosmetic.

> **Known flaw, disclose it yourself before she finds it:** we segmented with the pipeline's
> default `--rate 100` on 66 Hz data. A 2 s window then needs ≥100 packets to pass the fill
> check, so **48 of 370 possible windows (13%) were discarded**. Re-running with `--rate 50`
> recovers them with no recapture. Volunteering this makes everything else you say more
> credible.

---

## Part 3 — Architecture, layer by layer (§7)

### Exact shape trace (verify live in the notebook)

```
input                       (B, 52, 200)    B=batch, 52 subcarriers, 200 time steps
  Conv1d(52→64, k=5, pad=2)  (B, 64, 200)
  BatchNorm1d(64) + ReLU     (B, 64, 200)
  MaxPool1d(2)               (B, 64, 100)
  Conv1d(64→128, k=5, pad=2) (B, 128, 100)
  BatchNorm1d(128) + ReLU    (B, 128, 100)
  MaxPool1d(2)               (B, 128, 50)
transpose                    (B, 50, 128)   → (batch, time, features) for the GRU
  GRU(128→128, 2 layers, bidirectional)
                             (B, 50, 256)   256 = 128 hidden × 2 directions
  Linear(256→1) + softmax    (B, 50, 1)     attention weights, sum to 1 over time
  weighted sum over time     (B, 256)       context vector
  Linear(256→64)+ReLU+Dropout(0.5)+Linear(64→2)
                             (B, 2)         logits
```

### Parameter budget (printed in the notebook)

| Component | Parameters | Share |
|---|---:|---:|
| CNN feature extractor | 58,176 | 10.2% |
| **BiGRU** | **494,592** | **86.8%** |
| Attention | 257 | 0.05% |
| Classifier head | 16,578 | 2.9% |
| **Total** | **569,603** | 100% |

ResNet-18 (the ImgFi notebook backbone) = ~11.18 M → **19.6× larger than ours**.

> **If she asks "where do the parameters actually go?"** → 87% is the GRU. Say you know that,
> and that it is the obvious first target if the model needs to shrink (1 layer instead of 2,
> or hidden 64 instead of 128).

### THE key question: "Why is 52 the channel dimension?"

This is the question she is most likely to press on, and it is your best answer.

`nn.Conv1d(in_channels=52, out_channels=64, kernel_size=5)`:

- The **52 subcarriers are input channels**, like RGB is 3 channels in an image CNN.
- The kernel slides along **time only**.
- At each time step, every filter sees **all 52 subcarriers simultaneously**.
- So a filter can learn a pattern like *"subcarriers 10–20 rise while 35–45 fall"* — a
  **cross-subcarrier spatial signature** of the multipath geometry.

**ImgFi structurally cannot do this.** It makes one image per subcarrier, so each image sees
exactly one subcarrier, and majority voting at the end combines *decisions*, not *features*.
The joint pattern is destroyed by construction.

**And we proved the joint pattern is real (§3):**

| Measurement | `action` takes | `noaction` takes |
|---|---|---|
| Mean \|correlation\| between subcarriers | 0.38–0.45 | 0.18–0.40 |
| **Effective rank** (of 52) | **3.8** | 11.9 |

During motion the 52 subcarriers collapse to **≈4 independent dimensions**, because one
moving body imposes *one* dominant channel perturbation that all subcarriers see together.

**Two consequences — say both:**

1. ImgFi's "×52 free data expansion" is not ×52 of *information*. The 52 images per window
   are ~4 distinct views plus 48 near-duplicates. The effective dataset is closer to
   322 × 4 than 322 × 52.
2. The correlation *structure itself* is a feature — and it is exactly what our Conv1d reads
   and ImgFi discards.

> **Effective rank, if she asks the definition:** $\exp(H(\lambda))$ where $H$ is the Shannon
> entropy of the normalised eigenvalue spectrum of the covariance matrix. It is a continuous
> version of "how many dimensions actually matter". 52 equal eigenvalues → 52; one dominant
> eigenvalue → ≈1.

### Layer-by-layer rationale

**`Conv1d(52→64, kernel_size=5, padding=2)`**
- k=5 at the 100 Hz window grid = **50 ms**, the timescale of a limb movement.
- `padding=2` keeps length at 200 (`same` padding) so nothing is lost at the edges.
- 64 filters = 64 different learned cross-subcarrier patterns.

**`BatchNorm1d`** — subcarrier variances differ by orders of magnitude (frequency-selective
fading). Normalising per channel keeps gradients well-scaled and speeds convergence.

**`ReLU`** — nonlinearity; cheap, no vanishing gradient.

**`MaxPool1d(2)`** — halves time (200→100→50), keeps the strongest response in each pair,
gives small shift-invariance. After both pools, **each GRU time step = 40 ms of real time**,
and the CNN's receptive field is ≈13 original samples ≈ **130 ms**.

**`Conv1d(64→128)`** — second stage composes simple primitives into longer patterns
(a classic CNN hierarchy).

**`GRU(128→128, num_layers=2, bidirectional=True)`**
- *Why any RNN?* The CNN only sees ±130 ms. An activity is an **ordered sequence** — squat
  down, pause, come up. The GRU carries state across the whole 2 s and can represent order.
- *Why GRU not LSTM?* 3 gates instead of 4 → ~25% fewer parameters. With only ~130 training
  windows per fold, the smaller model is the right call. LSTM's extra cell state buys little
  at a 50-step sequence.
- *Why bidirectional?* We classify a **complete, already-recorded** window offline, so the
  end of the window is legitimately available when interpreting the beginning. **If she asks
  about real-time deployment:** correct — bidirectional adds latency, and for streaming we
  would switch to unidirectional or run it on a sliding buffer. Acknowledge it.
- *Why 2 layers?* One layer underfits the compositional structure; three overfits 130 samples.

**Attention: `Linear(256→1)` + softmax over time**
- *The problem it solves:* motion does not fill the window. A squat may occupy 0.6 s of 2 s.
  **Mean-pooling** would dilute the informative 0.6 s with 1.4 s of idle. **Last hidden state**
  would discard it entirely if it happened early.
- *The mechanism:* score each of the 50 time steps, softmax to weights summing to 1, take the
  weighted average. The model **learns which moments matter**.
- *Cost:* 257 parameters. Essentially free.

**And we verified it does something (§13):**
- Attention peak / uniform = **2.22×** (1.0 would mean flat = identical to mean-pooling).
- Correlation between attention weight and instantaneous motion energy = **+0.346** across all 182 test windows.

> That is the answer to *"you added attention, prove it isn't decoration."* We measured it.

**`Dropout(0.5)`** — 322 windows is tiny; 0.5 is aggressive regularisation, deliberately.

**`Linear(256→64→2)`** — small head, no reason for more capacity.

---

## Part 4 — Training and evaluation protocol (§9, §10)

| Setting | Value | Why |
|---|---|---|
| Loss | CrossEntropyLoss | standard for classification |
| Optimiser | Adam, lr 1e-3 | robust default; no time to tune on 322 samples |
| LR schedule | ExponentialLR γ=0.85 | smooth decay; loss plateaus by ~epoch 10 |
| Epochs | 30 | training accuracy saturates ~epoch 5; rest confirms stability |
| Batch | 32 | small dataset → small batch → more updates per epoch |
| Seed | fixed (0) | results are reproducible; the original run had no seed |

### The protocol question — Leave-One-Subject-Out

**Say this clearly, it is a strength:**

> "We never use a random split. All windows from one take are highly correlated — same
> person, same clothes, same position, seconds apart. A random split puts near-duplicates in
> both train and test and gives a meaningless 99%. We train on one person and test entirely
> on the other, in both directions, and we report the **worse** of the two."

Model selection uses a **validation set carved from the training subject's windows**
(15%, split by window). **The test subject is never used to choose anything.**

> **We are stricter than the published datasets we compare against:**
> ARIL tests on "every 5th sample" from the *same single volunteer*; UT-HAR splits randomly.
> Only Widar 3.0 has a comparably clean protocol.

---

## Part 5 — ImgFi: the paper, our notebook, and our model

She will ask *"the paper did X, why did you do Y?"* — so separate three different things.

### 5.1 What the ImgFi paper actually says

- Convert CSI time series to images; compares 5 methods (RP/RT, GASF, GADF, MTF, STFT).
- **RT (recurrence transform), $RT[i,j] = |x_i - x_j|$, scored best (~99.8%)** and is cheapest.
- **Core claim: a lightweight 3-conv-layer CNN matches ResNet-50/VGG-19 with ~90× fewer
  parameters.** The paper is fundamentally an *efficiency* argument.

### 5.2 What our ImgFi notebook actually did — and where it diverges

⚠️ **Know these before she does. They are all defensible if you raise them first.**

| Aspect | ImgFi notebook | Issue |
|---|---|---|
| Backbone | **ImageNet-pretrained ResNet-18 (11.2 M)** | The paper's whole point is a *lightweight 3-conv CNN*. Using ResNet-18 **contradicts the paper's thesis** — so it is not a reproduction of ImgFi, it is a recurrence-plot pipeline with a heavy off-the-shelf backbone |
| Windowing | slices **100 packets** assuming 50 Hz | Real rate is 51.5–77.6 Hz, so a "2 s" window is really **1.29–1.94 s** and varies per file. Windows are not physically comparable |
| Duration reporting | `rows / 50` | Reports amrith `mixed` as **158.6 s** when it is really **107.9 s** |
| Normalisation | `StandardScaler` fit on **all 8 files** | Test-subject statistics leak into the scaler |
| Model selection | evaluates on the **test set** every epoch, keeps the best | Test set influenced selection → the 97.8% "best" is optimistically biased |
| LOSO folds | only **1** (test = amrith) | The rishiikesh direction was never run |
| Normalisation constants | ImageNet mean/std on a replicated grayscale RP | Arbitrary for recurrence plots (harmless, but she may ask) |

**How to present this:** *"Our ImgFi notebook is a working recurrence-plot baseline, but it is
not a faithful reproduction of the paper and it has three protocol issues we identified. That
is precisely why we do not claim our model beats it on accuracy — the comparison isn't
like-for-like yet."* That is a much stronger position than defending a flawed comparison.

### 5.3 Head-to-head

| | ImgFi notebook | Ours |
|---|---|---|
| Representation | 52 RP images, 224×224 | raw 52×200 matrix |
| Subcarriers | **independent**, majority vote | **joint**, CNN input channels |
| Windowing | 100 packets (assumes 50 Hz) | 2 s wall-clock, timestamp-resampled |
| Normalisation | all files (leak) | train split only |
| Backbone | ResNet-18, 11.2 M | CNN-GRU-Attn, **0.57 M** |
| Forward passes/window | **52** | **1** |
| Temporal order | implicit (image diagonal) | explicit (BiGRU + attention) |
| Model selection | on test set | on validation split |
| LOSO folds | 1 | 2 |
| Accuracy | 95.9% final / 97.8% best (amrith) | **98.4%** (amrith), 98.6% (rishiikesh) |
| Inference | 52 × 224×224×3 passes | **0.55 ms**, one pass |

**Crucial caveat to state out loud:** the two pipelines segment differently — ImgFi produces
**497** windows of ~1.5 s average, we produce **322** windows of exactly 2 s. **Different
sample sets, so the accuracies are not directly comparable.** What *is* comparable and solid:
19.6× fewer parameters, 52× fewer forward passes, correct time-based windowing, no leakage,
honest model selection.

### 5.4 "So did you follow the paper or not?"

> "We follow the paper's *goal* — a lightweight model — but not its representation. The paper
> reached efficiency by keeping the image representation and shrinking the CNN. We reached it
> by dropping the image representation entirely: no 224×224 upsampling of a 200-point series,
> no 52× duplication of work. 0.57 M parameters is in the spirit of the paper's ~90× reduction
> claim. And we have a measurement the paper does not: on *our* hardware the 52 subcarriers
> carry only ~4 independent dimensions, which is what removes the benefit of treating them as
> 52 separate images."

---

## Part 6 — Results, and the honest interpretation (§10–§15)

### Headline

| Fold | Test windows | Accuracy | Confusion (rows=true) |
|---|---|---|---|
| test = amrith | 182 | **98.352%** | action 91/1 · noaction 2/88 |
| test = rishiikesh | 140 | **98.571%** | action 76/0 · noaction 2/62 |
| **Headline (worse)** | | **98.35%** | |

Precision/recall for `action`: 0.978/0.989 (amrith), 0.974/1.000 (rishiikesh).

### Per-activity breakdown — and a result that surprised us

| Take | n | Accuracy |
|---|---:|---:|
| walk | 87 | 1.000 |
| sit | 73 | 1.000 |
| mixed | 81 | 0.988 |
| **stand** | 81 | **0.951** |

**We expected `mixed` to be hardest** (it has the small drink/bend motions). It wasn't —
**`stand` was.** All `noaction` errors come from *standing still*, none from *sitting still*.

**Physical explanation:** a standing person is never truly static — postural sway, weight
shifts and breathing perturb the channel. A seated person is mechanically braced. So `stand`
windows sit closest to the decision boundary.

> Reporting a disproved hypothesis *with an explanation* is exactly the kind of thing that
> impresses a mentor. Do not hide it.

### The uncomfortable result — lead with it, don't get caught by it

**Baseline: one scalar (mean over subcarriers of temporal std = "motion energy"), one
threshold, chosen on the training subject only.**

| Fold | 1-feature baseline | CNN-GRU-Attention | Gap |
|---|---:|---:|---:|
| test = amrith | 98.35% | 98.35% | **0.00** |
| test = rishiikesh | **99.29%** | 98.57% | **−0.72** |

`action` windows carry **4.20×** the motion energy of `noaction` (0.01452 vs 0.00346).

**The deep model does not beat a one-line threshold. On one fold it is slightly worse.**

**How to say it:**

> "This does not mean the architecture is wrong — it means **this binary task is too easy to
> distinguish a good model from a trivial one**. Separating 'moving' from 'not moving' is a
> single-scalar problem. Our 98.4% validates the chain — capture, segmentation, subject-
> independent evaluation — not the architecture.
>
> The architecture's justification is *structural*, not this accuracy number: cross-subcarrier
> information exists and we exploit it (§3), our sampling rate covers the informative band
> (§4), attention is measurably non-uniform (§13), and we are 19.6× smaller with 52× fewer
> passes (§16). The real test is 7 classes, where a single energy scalar **cannot** separate
> `squat` from `bend` from `drink` — they have similar energy but different *temporal
> structure*, which is exactly what the GRU and attention encode."

### Sampling rate — the strongest single piece of analysis (§4)

She may say *"UT-HAR and Widar sample at 1000 Hz, you sample at 66 Hz — your data is
inadequate."* You have a measured answer:

- Doppler shift $f_d = 2vf_c/c$; at 2.462 GHz that is **16.4 Hz per m/s** of radial speed.
- We divided the `action` power spectrum by the `noaction` spectrum. **Above 18 Hz the ratio
  is 1.0** — the classes are indistinguishable there, that band is pure noise floor.
- **All class-discriminative information lies below 18 Hz.**
- Our worst-case Nyquist is **25.8 Hz**, median **34.1 Hz** → **1.43×–1.90× headroom**.

> "So the 15× rate deficit versus UT-HAR costs us nothing measurable *on this task*, and I can
> show the spectrum. **But** — this only holds because walk and mixed are gross whole-body
> motions. A fast hand at 3 m/s is 49 Hz and would alias. For the 7-class collection with
> `drink` and `nod`, we must repeat this exact test *before* bulk recording. It takes ten
> minutes."

That answer converts a suspected fatal flaw into evidence of rigour **plus** a concrete plan.

---

## Part 7 — Weaknesses: prepared answers

| Likely attack | Your answer |
|---|---|
| "98% is meaningless, task is trivial" | **Agree, and show §15 first.** One scalar gets the same. Explain what the number *does* validate, and that the structural justification is §3/§4/§13/§16. |
| "Only 2 subjects" | True and it is our biggest limitation. Each fold trains on one person. ARIL has 1 subject, UT-HAR 6, Widar 16. We need ≥5 subjects, ≥2 days, ≥2 geometries — it is item 7 on our fix list. |
| "Only 322 samples" | Correct — ARIL 1,394, UT-HAR 4,477, Widar 258,000. Plus we lost 13% to the `--rate 100` default, recoverable immediately. `--step 1.0` overlap would roughly double the rest. |
| "Why not use phase?" | Part 1 — CFO/SFO/timing, unsynchronised USRP. Widar's phase trick needs ≥2 antennas; we are SISO. ARIL discards phase even *with* GPS sync. |
| "Why not just use ResNet, it's proven?" | 19.6× the parameters and 52 forward passes per window for equal-or-worse accuracy on our data. Also our dataset is 322 windows — an 11 M-parameter model on that is asking to overfit. |
| "Your attention is decoration" | §13: peak/uniform 2.22×, correlation +0.346 with motion energy over 182 windows. Measured, not assumed. |
| "Bidirectional GRU can't work in real time" | Correct. We classify complete recorded windows offline, so it is valid here. For streaming we would switch to unidirectional or a sliding buffer — a known, accepted trade-off. |
| "Your two notebooks aren't comparable" | **Agree — say it before she does.** Different windowing (497 vs 322 windows, ~1.5 s vs exactly 2 s). What *is* comparable: parameters, forward passes, protocol cleanliness. |
| "Training accuracy hits 1.000 in 5 epochs — overfitting" | Yes, capacity far exceeds this task. Val stays 0.905–1.000 and test 98.4%, so it is not hurting *here*, but it is more evidence the task is too easy — same conclusion as §15. |
| "Why 2 s windows?" | Long enough to contain a full squat/bend cycle (~2–3 s per the capture protocol), short enough to give 322 samples from 752 s of capture. It is also what ImgFi and most CSI-HAR work uses, so it is comparable. |
| "Why did you drop rows?" | Exactly one truncated final row per file — the flowgraph was Ctrl+C'd mid-write. 0.015% of cells. We drop it explicitly rather than let NaN propagate. |

---

## Part 8 — Rapid-fire Q&A bank

**On CSI / the data**
- *How many subcarriers and why?* 52 — 802.11a/g 20 MHz, 64 FFT slots minus 12 null (DC+guards).
- *Sampling rate?* 51.5–77.6 Hz, mean 66.4. Passive sniffing, so it is whatever the link emits and `gr-ieee802-11` can decode (legacy OFDM only; 802.11n HT frames are undecodable).
- *Frequency?* 2.462 GHz, channel 11, 20 MHz bandwidth.
- *How many antennas?* One. SISO. That is why no phase-difference features.
- *Sample dimensions?* 52 × 200 = 2 s at the 100 Hz interpolation grid.
- *How many samples?* 322 windows: 168 action / 154 noaction.
- *Why interpolate onto a uniform grid?* Packets arrive irregularly (median gap 12 ms, worst 464 ms). Slicing by packet count would give windows of inconsistent physical duration — which is exactly what the ImgFi notebook does.

**On the model**
- *Total parameters?* 569,603. GRU is 87% of that.
- *Input to Conv1d?* 52 channels (subcarriers), sliding over time.
- *Kernel size 5 = how long?* 50 ms at the 100 Hz grid.
- *GRU sequence length?* 50 steps, each 40 ms → 2 s total.
- *GRU output width?* 256 = 128 hidden × 2 directions.
- *Attention parameters?* 257 (a single Linear(256→1)).
- *Inference time?* 0.55 ms per window, one forward pass.
- *Why GRU over LSTM?* ~25% fewer parameters at 50 steps; dataset is tiny.
- *Why dropout 0.5?* 322 windows — aggressive regularisation is deliberate.

**On evaluation**
- *Split?* Leave-one-subject-out, both directions, report the worse.
- *Why not random?* Adjacent windows from one take are near-duplicates → leakage → fake 99%.
- *Validation?* 15% of the *training* subject's windows, split by window. Test never used for selection.
- *Result?* 98.352% (amrith) / 98.571% (rishiikesh) → headline **98.35%**.
- *Baseline?* One scalar + one threshold: 98.35% / 99.29%. **The deep model does not beat it.**

**On ImgFi**
- *What is RT/RP?* $RT[i,j]=|x_i-x_j|$ — each pixel compares the signal at two moments, so the basic feature unit is a time-to-time relationship.
- *Why did the paper pick RT?* Best of its 5 methods (~99.8%) and cheapest to compute.
- *Why didn't you use it?* §3 — 52 subcarriers carry ~4 independent dimensions, so the ×52 image expansion is mostly duplication; and it costs 52 forward passes per window.
- *Did your ImgFi notebook follow the paper?* No — it uses ImageNet-pretrained ResNet-18, whereas the paper's central claim is a lightweight 3-conv CNN. Be upfront.

---

## Part 9 — What to show, in order

Walk the notebook top to bottom; it is deliberately ordered as an argument.

| Show | Section | The one sentence to say |
|---|---|---|
| 1 | §1 raw CSI + rate table | "This is the raw sensor output; we measure 66 Hz, and duration comes from timestamps, not row counts." |
| 2 | §1 heatmap | "Vertical stripes = one event hitting all 52 subcarriers together." |
| 3 | §2 window + RPs | "This is the model's input, and this is what ImgFi would turn it into." |
| 4 | §2 six-subcarrier RP strip | "These six images are near-duplicates — that motivates the next section." |
| 5 | **§3 effective rank** | "≈4 independent dimensions, not 52. This is why we process jointly." |
| 6 | **§4 spectral ratio** | "All class information is below 18 Hz; our Nyquist is 25.8 Hz. The rate is sufficient — measured, not assumed." |
| 7 | §5 dataset + the 13% disclosure | "322 windows, balanced, LOSO. And here is a mistake we found ourselves." |
| 8 | §7 shape trace + parameters | "52 subcarriers are the channel dimension — here is the tensor at every stage." |
| 9 | §10–12 results + confusion | "98.35% headline, worse of two folds." |
| 10 | **§13 attention** | "2.22× non-uniform, +0.346 correlation with motion energy — it is doing something." |
| 11 | §14 per-take | "`stand` is hardest, not `mixed` — here is why we think that is." |
| 12 | **§15 baseline** | "And here is the honest part: one scalar does just as well." |
| 13 | §16–17 efficiency + comparison | "19.6× fewer parameters, 1 pass instead of 52 — and here is why the accuracies aren't directly comparable." |
| 14 | §18 limitations | "These are the six things wrong with this dataset." |

---

## Part 10 — The closing statement

> "The pilot did exactly what a pilot is for. The capture chain works, the evaluation is
> leakage-free and stricter than ARIL's or UT-HAR's, and we found and fixed real problems —
> the 13% window loss, the normalisation leak, the test-set model selection.
>
> What we deliberately do **not** claim is that 98.4% proves our architecture. A single
> threshold matches it, because separating moving from still is a one-scalar problem. What we
> do claim is structural: cross-subcarrier information exists and we exploit it, our sampling
> rate provably covers the informative band, attention is measurably active, and we do it with
> 0.57 M parameters and one forward pass instead of 11.2 M and 52.
>
> The next step is the 7-class collection, where a single energy scalar cannot work — and
> before we record it, we will run the ten-minute spectral test on `nod` and `drink`, because
> that is the one place this hardware is most likely to fail."

---

## Appendix — every number, one place

| Quantity | Value |
|---|---|
| Subcarriers | 52 (802.11a/g, 20 MHz, 64 FFT − 12 null) |
| Carrier / channel | 2.462 GHz, ch 11 |
| Antennas | 1 (SISO) |
| Packet rate | 51.5–77.6 Hz, mean 66.4 |
| Median inter-packet gap / worst | 12 ms / 464 ms |
| Window | 2 s → 52 × 200 (100 Hz grid) |
| Windows | 322 (168 action / 154 noaction), 52.2% action |
| Per subject | amrith 182, rishiikesh 140 |
| Per take | walk 87, mixed 81, stand 81, sit 73 |
| Windows lost to `--rate 100` | 48 of 370 (13.0%) |
| Truncated rows | 1 per file (0.015% of cells) |
| Mean \|subcarrier corr\| (action) | 0.38–0.45 |
| **Effective rank** | **3.8 (action) / 11.9 (noaction)** of 52 |
| **Discriminative band** | **< 18 Hz** |
| Nyquist (worst / median) | 25.8 / 34.1 Hz → 1.43× / 1.90× headroom |
| Doppler scaling | 16.4 Hz per m/s |
| Parameters | 569,603 (CNN 58,176 · GRU 494,592 · attn 257 · head 16,578) |
| ResNet-18 comparison | ~11.18 M → 19.6× larger |
| Inference | 0.55 ms/window, 1 pass (vs 52) |
| **LOSO accuracy** | **98.352% (amrith) / 98.571% (rishiikesh)** |
| F1 (action) | 0.984 / 0.987 |
| Per-take accuracy | walk 1.000, sit 1.000, mixed 0.988, **stand 0.951** |
| Attention peak/uniform | 2.22× |
| Attention–energy correlation | +0.346 |
| **1-feature baseline** | **98.35% / 99.29%** |
| Motion energy | action 0.01452, noaction 0.00346 → **4.20×** |
| ImgFi notebook windows | 497 (270 action / 227 noaction) |
| ImgFi notebook accuracy | 95.94% final, 97.79% best (amrith only) |
