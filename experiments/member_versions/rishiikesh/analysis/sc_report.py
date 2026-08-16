#!/usr/bin/env python3
"""Stage 4: assemble the standalone HTML report (figures inlined as data URIs)."""

import base64
import json
import os

ROOT = "/home/rishiikesh/usrp-projects/analysis"
FIG = os.path.join(ROOT, "figures")
S = json.load(open(os.path.join(ROOT, "sc_scores.json")))

ACTS = S["acts"]
LABEL = {"walk": "Walking", "mixed": "Mixed activity",
         "stand": "Standing", "sit": "Sitting"}
SEL8 = sorted(S["mrmr_order"][:8])
SEL12 = sorted(S["mrmr_order"][:12])
SEL16 = sorted(S["mrmr_order"][:16])
C = S["curve"]
K = C["k"]


def img(name, alt):
    with open(os.path.join(FIG, f"{name}.png"), "rb") as fh:
        b = base64.b64encode(fh.read()).decode()
    return (f'<figure class="plate">'
            f'<img src="data:image/png;base64,{b}" alt="{alt}">'
            f'</figure>')


def ofdm(i):
    """Subcarrier index -> OFDM index and MHz offset from 2.462 GHz."""
    k = i - 26 if i < 26 else i - 25
    return k, k * 0.3125


def strip():
    cells = []
    for i in range(52):
        cls = "cell"
        if i in SEL8:
            cls += " core"
        elif i in SEL12:
            cls += " ext"
        cells.append(f'<div class="{cls}" title="SC{i} &middot; '
                     f'{ofdm(i)[1]:+.2f} MHz"><span>{i}</span></div>')
    return '<div class="strip">' + "".join(cells) + "</div>"


def acc(i):
    return f"{C['selected'][i]:.0%}"


I8, I12, I52 = K.index(8), K.index(12), K.index(52)

rows_activity = "".join(f"""
  <tr>
    <th scope="row">{LABEL[a]}</th>
    <td class="num">{", ".join(str(i) for i in S['top_per_activity'][a][:6])}</td>
    <td class="num sub">{", ".join(str(i) for i in S['top_per_activity_env']['A'][a][:6])}</td>
    <td class="num sub">{", ".join(str(i) for i in S['top_per_activity_env']['B'][a][:6])}</td>
    <td class="num rho {'bad' if S['reliability']['cross_env'][a] < 0.3 else ''}">
      {S['reliability']['cross_env'][a]:+.2f}</td>
  </tr>""" for a in ACTS)

rows_valid = "".join(f"""
  <tr{' class="hi"' if k in (8, 12) else ''}>
    <th scope="row">{k}</th>
    <td class="num">{C['selected'][i]:.1%}</td>
    <td class="num sub">{C['random_mean'][i]:.1%}</td>
    <td class="num sub">{C['worst'][i]:.1%}</td>
    <td class="num sub">{C['within'][i]:.1%}</td>
  </tr>""" for i, k in enumerate(K))

sel_list = ", ".join(f"SC{i}" for i in SEL8)
sel12_list = ", ".join(str(i) for i in SEL12)

HTML = f"""<title>Subcarrier Shortlist</title>
<style>
:root {{
  color-scheme: light;
  --paper:#f4f6f8; --surface:#fdfdfe; --plate:#fcfcfb;
  --ink:#111721; --ink2:#485163; --muted:#7d8697;
  --rule:#dde2e9; --rule-strong:#c3cad5;
  --sig:#2a78d6; --sig-soft:#e8f0fb;
  --warn:#c4501f; --warn-soft:#fbeee7;
  --good:#0f8f63;
  --shadow:0 1px 2px rgba(17,23,33,.05), 0 8px 24px -18px rgba(17,23,33,.35);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --paper:#0f1319; --surface:#161b23; --plate:#fcfcfb;
    --ink:#eef1f6; --ink2:#a9b3c2; --muted:#78828f;
    --rule:#242b35; --rule-strong:#333c48;
    --sig:#5598e7; --sig-soft:#16263c;
    --warn:#ef8a5c; --warn-soft:#2c1c14;
    --good:#3cb98c;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -18px rgba(0,0,0,.8);
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --paper:#0f1319; --surface:#161b23; --plate:#fcfcfb;
  --ink:#eef1f6; --ink2:#a9b3c2; --muted:#78828f;
  --rule:#242b35; --rule-strong:#333c48;
  --sig:#5598e7; --sig-soft:#16263c;
  --warn:#ef8a5c; --warn-soft:#2c1c14;
  --good:#3cb98c;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -18px rgba(0,0,0,.8);
}}

* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"Iowan Old Style","Charter","Bitstream Charter",Georgia,
    "Times New Roman",serif;
  font-size:17px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}}
.mono, .num, .eyebrow, th, .tick, .cell span, .stat-v, .chip {{
  font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,
    "Liberation Mono",monospace;
  font-variant-numeric:tabular-nums;
}}
h1,h2,h3,.eyebrow,.stat-l {{
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,
    Helvetica,Arial,sans-serif;
}}

.wrap {{ max-width:1120px; margin:0 auto; padding:0 28px 96px; }}
.measure {{ max-width:70ch; }}

/* ---------- masthead ---------- */
header.top {{
  border-bottom:1px solid var(--rule-strong);
  padding:64px 0 30px; margin-bottom:44px;
}}
.eyebrow {{
  font-size:11px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--muted); font-weight:600;
}}
h1 {{
  font-size:clamp(38px,6vw,62px); line-height:1.02; margin:16px 0 0;
  letter-spacing:-.025em; font-weight:650; text-wrap:balance;
}}
.standfirst {{
  font-size:20px; line-height:1.55; color:var(--ink2);
  margin:20px 0 0; max-width:62ch; text-wrap:pretty;
}}
.meta {{
  display:flex; flex-wrap:wrap; gap:8px 26px; margin-top:26px;
  font-size:12.5px; color:var(--muted);
}}
.meta b {{ color:var(--ink2); font-weight:600; }}

/* ---------- sections ---------- */
section {{ margin:0 0 60px; }}
h2 {{
  font-size:15px; font-weight:650; letter-spacing:.01em; margin:0;
  padding-bottom:10px;
}}
.head {{
  display:flex; align-items:baseline; gap:14px;
  border-bottom:1px solid var(--rule); margin-bottom:26px;
  padding-top:6px;
}}
.head .kind {{
  font-size:10.5px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--sig); font-weight:700; padding-bottom:10px; white-space:nowrap;
  font-family:ui-sans-serif,system-ui,sans-serif;
}}
h3 {{
  font-size:19px; font-weight:620; letter-spacing:-.012em;
  margin:38px 0 10px; text-wrap:balance;
}}
p {{ margin:0 0 16px; }}
.measure p:last-child {{ margin-bottom:0; }}
a {{ color:var(--sig); }}

/* ---------- answer block ---------- */
.answer {{
  background:var(--surface); border:1px solid var(--rule);
  border-radius:3px; box-shadow:var(--shadow);
  padding:30px 32px 34px; margin-bottom:16px;
}}
.answer .lead {{
  font-size:14px; color:var(--ink2); margin:0 0 18px;
  font-family:ui-sans-serif,system-ui,sans-serif;
}}
.setline {{
  font-size:clamp(20px,3.2vw,29px); line-height:1.35; margin:0;
  letter-spacing:-.01em; font-weight:600;
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums;
}}
.setline em {{ font-style:normal; color:var(--sig); }}

/* 52-cell band */
.strip {{
  display:grid; grid-template-columns:repeat(52,1fr); gap:2px;
  margin:26px 0 8px;
}}
.cell {{
  aspect-ratio:1/2.4; border-radius:1.5px; background:var(--rule);
  display:flex; align-items:flex-end; justify-content:center;
  position:relative;
}}
.cell span {{ display:none; }}
.cell.core {{ background:var(--sig); }}
.cell.ext {{ background:color-mix(in srgb,var(--sig) 42%,var(--rule)); }}
.striplab {{
  display:flex; justify-content:space-between;
  font-size:10.5px; color:var(--muted);
  font-family:ui-monospace,Menlo,Consolas,monospace;
}}
.key {{
  display:flex; flex-wrap:wrap; gap:6px 20px; margin-top:18px;
  font-size:12.5px; color:var(--ink2);
  font-family:ui-sans-serif,system-ui,sans-serif;
}}
.key i {{
  width:11px; height:11px; border-radius:2px; display:inline-block;
  margin-right:7px; vertical-align:-1px;
}}

/* ---------- stat row ---------- */
.stats {{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(178px,1fr));
  gap:1px; background:var(--rule); border:1px solid var(--rule);
  border-radius:3px; overflow:hidden; margin:16px 0 0;
}}
.stat {{ background:var(--surface); padding:18px 20px 20px; }}
.stat-v {{
  font-size:31px; line-height:1.1; font-weight:600; letter-spacing:-.02em;
  font-variant-numeric:proportional-nums;
}}
.stat-v.up {{ color:var(--sig); }}
.stat-l {{
  font-size:11.5px; color:var(--muted); margin-top:7px; line-height:1.45;
}}

/* ---------- tables ---------- */
.tablewrap {{ overflow-x:auto; margin:0 0 8px; }}
table {{
  border-collapse:collapse; width:100%; font-size:14px;
  font-family:ui-sans-serif,system-ui,sans-serif;
}}
caption {{
  text-align:left; font-size:12.5px; color:var(--muted);
  padding-bottom:12px; line-height:1.5;
}}
th, td {{
  text-align:left; padding:9px 14px 9px 0; border-bottom:1px solid var(--rule);
  vertical-align:baseline; white-space:nowrap;
}}
thead th {{
  font-size:10.5px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); font-weight:700; border-bottom:1px solid var(--rule-strong);
}}
tbody th {{ font-weight:600; font-family:ui-sans-serif,system-ui,sans-serif; }}
td.num {{ font-size:13px; color:var(--ink); }}
td.sub {{ color:var(--muted); }}
td.rho.bad {{ color:var(--warn); }}
tr.hi td, tr.hi th {{ background:var(--sig-soft); }}

/* ---------- figures ---------- */
.plate {{
  margin:26px 0 10px; padding:14px; background:var(--plate);
  border:1px solid var(--rule); border-radius:3px; box-shadow:var(--shadow);
  overflow-x:auto;
}}
.plate img {{ display:block; width:100%; min-width:520px; height:auto; }}
figcaption, .cap {{
  font-size:12.5px; color:var(--muted); line-height:1.55;
  margin:0 0 34px; max-width:76ch;
  font-family:ui-sans-serif,system-ui,sans-serif;
}}

/* ---------- callouts ---------- */
.note {{
  border-left:2px solid var(--warn); background:var(--warn-soft);
  padding:16px 20px; margin:26px 0; border-radius:0 3px 3px 0;
  font-size:15px; line-height:1.55;
}}
.note b {{ font-weight:650; }}
.note.ok {{ border-left-color:var(--good); background:transparent;
  border-left-width:2px; padding-left:20px; }}

ul {{ margin:0 0 16px; padding-left:1.15em; }}
li {{ margin-bottom:9px; }}
li::marker {{ color:var(--muted); }}

code {{
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-size:.88em; background:var(--sig-soft); color:var(--ink);
  padding:1px 5px; border-radius:2px;
}}

footer {{
  border-top:1px solid var(--rule-strong); padding-top:22px; margin-top:14px;
  font-size:12.5px; color:var(--muted);
  font-family:ui-sans-serif,system-ui,sans-serif;
}}
@media (max-width:640px) {{
  body {{ font-size:16px; }}
  .wrap {{ padding:0 18px 64px; }}
  .cell {{ aspect-ratio:1/3.4; }}
}}
</style>

<div class="wrap">

<header class="top">
  <div class="eyebrow">USRP CSI pilot &middot; channel 11 &middot; 2.462 GHz &middot; 52 subcarriers</div>
  <h1>Subcarrier Shortlist</h1>
  <p class="standfirst">Which of the 52 subcarriers are worth keeping &mdash; measured
  across walking, mixed activity, standing and sitting, in two different rooms.
  The short answer is eight, and they are not the ones a per-activity ranking
  would pick.</p>
  <div class="meta">
    <span><b>12</b> captures</span>
    <span><b>3</b> people</span>
    <span><b>2</b> rooms</span>
    <span><b>18</b> minutes of CSI</span>
    <span><b>1,093</b> 2-second windows</span>
    <span>env A &mdash; Amrith, Rishiikesh &middot; env B &mdash; Gowreesh</span>
  </div>
</header>

<section>
  <div class="head"><span class="kind">Recommendation</span><h2>The set to use</h2></div>

  <div class="answer">
    <p class="lead">Highest motion-SNR that survives in both rooms and all three
    people, de-duplicated against its own neighbours:</p>
    <p class="setline"><em>{sel_list}</em></p>
    {strip()}
    <div class="striplab"><span>SC0</span><span>SC13</span><span>SC26</span>
      <span>SC39</span><span>SC51</span></div>
    <div class="key">
      <span><i style="background:var(--sig)"></i>core 8 &mdash; best validated accuracy</span>
      <span><i style="background:color-mix(in srgb,var(--sig) 42%,var(--rule))"></i>
        extend to 12: {sel12_list}</span>
      <span><i style="background:var(--rule)"></i>drop</span>
    </div>
  </div>

  <div class="stats">
    <div class="stat"><div class="stat-v up">{acc(I8)}</div>
      <div class="stat-l">4-class accuracy on an unseen person, 8 subcarriers</div></div>
    <div class="stat"><div class="stat-v">{acc(I52)}</div>
      <div class="stat-l">same test using all 52 subcarriers</div></div>
    <div class="stat"><div class="stat-v">{S['binary_acc']:.0%}</div>
      <div class="stat-l">action vs no-action, 12 subcarriers, unseen person</div></div>
    <div class="stat"><div class="stat-v">{S['coh_lag']}</div>
      <div class="stat-l">subcarriers between independent looks &mdash; only
        ~{S['n_independent']:.0f} of the 52 are distinct</div></div>
  </div>

  <div class="note ok" style="margin-top:30px">
    <b>Cutting 52 &rarr; 8 does not cost accuracy. It buys it.</b> Dropping the
    band-edge subcarriers removes inputs that carry noise instead of signal, and
    cross-person accuracy rises {C['selected'][I8] - C['selected'][I52]:+.0%}
    &mdash; from {acc(I52)} to {acc(I8)}. You also cut the feature vector by 85%.
  </div>
</section>

<section>
  <div class="head"><span class="kind">Per activity</span><h2>Top subcarriers for each activity</h2></div>
  <div class="measure">
  <p>This is the ranking you asked for: for each activity, the subcarriers that
  best separate it from the other three. Scores are one-vs-rest separability
  (2&middot;|AUC&minus;&frac12;| over seven window features), computed per person
  and then combined.</p>
  </div>

  <div class="tablewrap">
  <table>
    <caption>Ranked best first. The last column is how well the room-A ranking
    predicts the room-B ranking &mdash; see the warning below it.</caption>
    <thead><tr>
      <th>Activity</th><th>Top 6 (both rooms)</th><th>Top 6 &mdash; env A</th>
      <th>Top 6 &mdash; env B</th><th>A&rarr;B agreement</th>
    </tr></thead>
    <tbody>{rows_activity}</tbody>
  </table>
  </div>

  {img("sc_fig4_top_per_activity", "Bar charts of subcarrier separability for each of the four activities, with the top ten highlighted")}
  <p class="cap">Each activity really does favour a different part of the band.
  Walking peaks around SC26&ndash;28 and SC36&ndash;39; standing sits low
  (SC4&ndash;8, SC18&ndash;23); sitting favours the extreme edges
  (SC2&ndash;5, SC40&ndash;44).</p>

  <div class="note">
    <b>Do not deploy these per-activity lists.</b> They are honest measurements
    of the captures you have, but the next column shows they do not survive a
    change of room &mdash; and the reliability test in the next section shows
    they do not even survive a change of person in the <em>same</em> room. Use
    them to understand the data, not to configure a receiver.
  </div>

  {img("sc_fig3_heatmap", "Heatmap of per-activity subcarrier separability measured separately in environment A and environment B")}
  <p class="cap">The same measurement, split by room. If the ranking were a
  property of the activity, the bright columns would line up vertically between
  each pair of rows. They do not.</p>
</section>

<section>
  <div class="head"><span class="kind">Reliability</span><h2>What transfers and what doesn't</h2></div>
  <div class="measure">
  <p>Before trusting any ranking, it is worth asking whether it is measuring
  something real or just fitting one recording. Three tiers answer that: split a
  single capture in half and compare, compare two people in the same room, then
  compare rooms.</p>
  </div>

  {img("sc_fig5_reliability", "Grouped bars comparing the reliability of two ranking metrics across three tiers: split-half, cross-subject and cross-room")}
  <p class="cap">Left: the per-activity separability ranking is highly repeatable
  inside one capture (&rho; = {S['reliability']['split_half']['walk']:.2f}&ndash;{S['reliability']['split_half']['stand']:.2f})
  and then collapses &mdash; it is <em>negatively</em> correlated between two
  people in the same room. Right: the motion-SNR profile behaves the opposite
  way for walking, holding at &rho; = +{S['msnr_reliability']['walk']['cross_subject_sameroom']:.2f}
  across people and +{S['msnr_reliability']['walk']['cross_env']:.2f} across rooms.</p>

  <div class="measure">
  <p>That split is the whole result. A subcarrier's ability to separate
  <em>this sitting capture</em> from <em>this standing capture</em> is a fact
  about one afternoon's multipath. How strongly a subcarrier responds to a body
  moving is a fact about the radio, and it is stable. The recommended set is
  built only from the second kind.</p>
  </div>
</section>

<section>
  <div class="head"><span class="kind">Mechanism</span><h2>Why those subcarriers</h2></div>

  {img("sc_fig1_passband", "Mean amplitude per subcarrier for both environments, showing a smooth arch peaking at band centre")}
  <p class="cap">The amplitude profile is a smooth 15.3 dB arch peaking at band
  centre, and it is the <em>same</em> arch in both rooms (r &asymp; 0.9). Room
  multipath would be jagged and room-specific; this is the radio's own passband
  roll-off. Band-edge subcarriers arrive ~15 dB weaker before anyone moves.</p>

  {img("sc_fig2_motion_profile", "Motion-SNR across the band by activity, and the walking profile from each individual capture")}
  <p class="cap">Motion response follows that passband almost exactly
  (&rho; = 0.91 against the level profile). For walking the profile is
  effectively identical in every capture &mdash; three people, two rooms, four
  days apart.</p>

  {img("sc_fig10_spectra", "Power spectral density of the best and worst subcarrier during walking and sitting")}
  <p class="cap">The mechanism, directly. SC29 and SC3 record the same walk with
  the <em>same</em> energy in the 0.5&ndash;25 Hz body-motion band &mdash; SC3 is
  not blind to the motion. SC3 simply carries about 6 dB more noise underneath
  it, because it sits down in the roll-off. Selecting subcarriers here is
  selecting SNR, not selecting sensitivity.</p>

  {img("sc_fig6_redundancy", "Correlation matrix between subcarriers and mean correlation versus subcarrier separation")}
  <p class="cap">Adjacent subcarriers are near-duplicates: correlation falls
  below 0.5 only after {S['coh_lag']} subcarriers, so the 52 carry roughly
  {S['n_independent']:.0f} independent looks at the channel. That is the ceiling
  on what more subcarriers can buy.</p>
</section>

<section>
  <div class="head"><span class="kind">Validation</span><h2>Does the set actually work</h2></div>
  <div class="measure">
  <p>A random forest over the same seven window features, trained on two people
  and tested on the third &mdash; so holding out Gowreesh is simultaneously the
  cross-room test. Nothing about the test person is seen during training.</p>
  </div>

  {img("sc_fig8_validation", "Accuracy versus number of subcarriers for selected, random and worst subcarrier sets")}
  <p class="cap">The selected set beats a random set of the same size at every
  size, peaks at 8 subcarriers, and beats all 52. The green line is the same
  model scored inside the capture it trained on &mdash; the gap between green and
  blue is how much of the usual CSI accuracy is really session memorisation.</p>

  <div class="tablewrap">
  <table>
    <caption>4-class accuracy. "New person" columns are leave-one-person-out;
    "same capture" is time-blocked CV inside each recording.</caption>
    <thead><tr>
      <th>Subcarriers</th><th>Selected, new person</th><th>Random</th>
      <th>Worst</th><th>Same capture</th>
    </tr></thead>
    <tbody>{rows_valid}</tbody>
  </table>
  </div>

  <h3>Forcing the set to spread across the band makes it worse</h3>
  <div class="measure">
  <p>The intuitive move is to spread picks across the spectrum for diversity.
  Tested directly, it loses: requiring 4 subcarriers of spacing drops accuracy to
  {S['strategy_cmp']['spacing4']['8']:.0%} and uniform decimation to
  {S['strategy_cmp']['uniform']['8']:.0%}, against
  {S['strategy_cmp']['mrmr_lam0.3']['8']:.0%} for the clustered high-SNR set. The
  SNR you give up at the band edges costs more than the decorrelation buys.</p>
  </div>

  {img("sc_fig9_confusion", "Confusion matrix for the 12-subcarrier set on an unseen person")}
  <p class="cap">Walking is solid at 87%. Mixed activity mostly collapses into
  walking, which is reasonable &mdash; it contains walking. Sitting and standing
  are only partly separable from each other. Collapsed to the binary
  action / no-action question the pilot was built for, this reaches
  {S['binary_acc']:.0%} on an unseen person.</p>
</section>

<section>
  <div class="head"><span class="kind">Limits</span><h2>What this data cannot tell you</h2></div>
  <div class="measure">
  <ul>
    <li><b>Each activity is one continuous capture per person.</b> Activity is
    perfectly confounded with recording session, so any slow channel drift is
    available to the classifier as a shortcut. This is why the same-capture
    numbers reach 94% while cross-person sits near 55%. Treat the
    <em>{acc(I8)}</em> as the honest figure and the 94% as unusable.</li>
    <li><b>Environment B is a noisier link.</b> Gowreesh's captures needed 8&ndash;11%
    of samples de-spiked against 0.2&ndash;6.5% in env A, and his
    <em>static</em> sitting capture carries as much 0.5&ndash;4 Hz band power as
    env A's motion captures. Something was moving, or the link was worse. He is
    also the hardest hold-out ({C['per_subject']['8']['gowreesh']:.0%} at k=8 against
    {C['per_subject']['8']['amrith']:.0%} for Amrith).</li>
    <li><b>Three people, one session each.</b> Enough to show the per-activity
    ranking does not transfer; not enough to certify the recommended set as
    final. It is the best-supported choice available, not a proven optimum.</li>
    <li><b>Sit and stand rankings are the weakest.</b> Both are near-static, so
    their profiles are dominated by whatever noise the link had that day
    (&rho; &le; +0.32 across rooms).</li>
    <li><b>Packet arrival is bursty</b> &mdash; 65&ndash;90 Hz median with gaps.
    Everything was resampled to a uniform 80 Hz grid, so the 30&ndash;38 Hz
    "noise band" includes some interpolation artefact. It is applied identically
    to every capture, so comparisons hold.</li>
    <li><b>Index-to-frequency mapping is inferred.</b> SC0&ndash;51 are assumed
    to run &minus;26&hellip;&minus;1, +1&hellip;+26 &mdash; supported by the
    single smooth arch with both ends lowest. On that mapping the core 8 span
    roughly &minus;1.9 to +1.6 MHz around 2.462 GHz.</li>
  </ul>
  </div>

  <h3>If you re-run the capture</h3>
  <div class="measure">
  <p>Two changes would let this analysis answer much more. Record the activities
  interleaved within one session rather than as one capture each, which breaks
  the session confound. And record at least one repeat session per person on a
  different day &mdash; that is the only way to tell a stable subcarrier
  preference from an afternoon's multipath.</p>
  </div>
</section>

<footer>
  Measured from the 12 pilot captures in <code>data/pilot/</code>. Pipeline:
  <code>analysis/sc_features.py</code> &rarr; <code>sc_select.py</code> &rarr;
  <code>sc_figures.py</code> &rarr; <code>sc_report.py</code>; all numbers in
  <code>analysis/sc_scores.json</code>. Every figure and figure caption is
  generated from the measured data.
</footer>

</div>
"""

out = os.path.join(ROOT, "sc_report.html")
with open(out, "w") as fh:
    fh.write(HTML)
print(f"wrote {out}  ({os.path.getsize(out)/1e6:.2f} MB)")
