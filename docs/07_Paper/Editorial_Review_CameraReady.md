# IEEE Access Camera-Ready Editorial Review

> ## STATUS — Critical pass + partial Major pass applied 2026-08-06
>
> Verified by rebuilding both the original (`git archive HEAD`) and the current
> tree on the same toolchain:
>
> | | Original | Now |
> |---|---|---|
> | Pages | 13 | **15** |
> | Body words (I–IX) | 5,564 | **9,498** |
> | References | 13 | **35** |
> | **Content overflow warnings** | **17** | **2** |
> | — objects clipped at the trim edge | 5 | **0** |
> | Figure width overflows | 8 | **0** |
> | Table width overflows | 5 | **0** |
> | Text/table overprints | 1 (p7) | **0** |
> | Figure-internal label overprints | 3 | **0** |
> | Placeholder figures | 2 | **0** |
> | *(TBD)* markers in Results | 5 | **0** |
> | Single-column : double-column figures | 0 : 8 | **3 : 2** |
> | Algorithm boxes | 0 | **2** |
> | Theorem-family environments | 0 | **3** |
> | Tables | 9 | **11** |
> | Type 3 (bitmap) fonts embedded | 3 | **0** |
> | Pages below 60% text density | 6 | **0** |
>
> **Critical — done:** C1 (figure widths + single/double reassignment), C2
> (Tables 1, 2, 4, 6 → `table*`; Tables 3 and 7 also fixed), C3 (reframed as a
> methodology paper: placeholders and §VI-D deleted, abstract and title
> rewritten to lead with the instrument, pre-registration protocol moved into
> Methodology as §V-E + Table 6), C4/C5 (figure overprints and internal titles),
> C7 (equation 5 split).
>
> **Major — done:** M1 (Related Work 861→1,743 words, five subsections,
> `\paragraph`→`\subsection`, 13→35 references), M2 (Discussion 247→916 with
> four subsections), M3 (Algorithms 1 and 2), M4 (Definition 1, Proposition 1,
> Remark 1), M5 (Introduction 516→957 with a six-item numbered contributions
> list), M7 (D3 figure → Table 9), M10 (Threats 444→795, restructured into
> detected / bounded / scope-restriction groups; Conclusion 159→455).
>
> **Major — outstanding:** M6 (merge Figs. 3+4 into one two-panel figure), M8
> (four of the six new tables), M9 (the twelve new figures of Part 3), M11
> (appendix consolidation 7→5).
>
> **Not done — blocked on author input:** C6. `\history` dates, `\doi`
> (assigned at submission), the `\tfootnote` funding statement, the
> Acknowledgment, and both biographies still contain placeholder text that is
> visible in the rendered PDF. These cannot be fabricated.
>
> **One extra defect found and fixed during the pass, not in the original
> report.** The manuscript embedded **3 Type 3 (bitmap) fonts**, which IEEE PDF
> eXpress rejects outright. Cause: the preamble overrode `\ttdefault` to `cmtt`
> to work around a missing Courier T1 metric, but T1-encoded `cmtt` has no
> Type 1 outline, so TeX silently generated EC bitmaps. Switched to `lmtt`
> (Latin Modern Mono), which ships real T1 Type 1 outlines. All fonts in the
> PDF are now Type 1.
>
> **Two corrections to the baseline recorded below.** The original content
> overflow count was **17**, not 13 — §0.1's table was measured on a build in
> which the bundled Type1 fonts had not resolved, which suppressed some
> warnings and altered two magnitudes (equation 5 is 47.50pt, not 43.22pt; a
> 12.17pt overflow in Table 7 was missed). Every defect named in §1 is real and
> was confirmed against the rendered pages. Separately, the log also carries 25
> `Overfull \hbox (505.12177pt)` warnings "while `\output` is active"; these are
> a **pre-existing artifact of the IEEE Access class's full-width page header**
> (27 of them in the original build), are not caused by any content, and have no
> visible effect on the rendered page.
>
> **Build.** `docs/07_Paper/build.sh` now compiles the manuscript reproducibly.
> This matters more than it sounds: the class ships its own Times/Formata Type1
> fonts in `ieeeaccess_support/`, and `.tfm` files resolve via `TFMFONTS` (not
> `TEXINPUTS`). Setting only `TEXINPUTS` compiles **without error** but drops
> every roman glyph to `nullfont`, silently producing a 6-page PDF containing
> only mathematics. Anyone rebuilding this paper needs that script.


**Manuscript:** *Lineage or Era? An Identifiability-Gated Variance Decomposition of Correlated Errors in Public Language Models*
**Reviewed build:** `docs/07_Paper/manuscript.pdf`, 13 pages, compiled from `manuscript.tex` (1,061 lines)
**Review date:** 2026-08-06
**Reviewing roles:** Associate Editor · Production Editor · Typesetter · Reviewer #1 (Statistics) · Reviewer #2 (Machine Learning) · Copy Editor
**Posture:** adversarial. Assume competition against the top 5% of IEEE Access submissions.

---

## 0. VERDICT — READ THIS BEFORE ANYTHING ELSE

The brief I was given was "polish this from 13 pages to 18–20 pages." That brief is wrong, and acting on it first would be a serious mistake.

**This manuscript would not reach peer review in its current state.** It would be stopped at administrative validation or desk-rejected by the Associate Editor within ten minutes, for three reasons that have nothing to do with length:

1. **Two pages of the paper are literally blank rectangles reading "FIGURE PLACEHOLDER — Final figure to be added by the authors."** Page 12 is 90% placeholder boxes. It contains 985 characters of real text — one-sixth of a normal page. No production editor forwards this.
2. **Five of the nine tables and all eight figures physically run off the text block, and two of them run off the trimmed page edge.** I measured this from the compile log, not by eye. Table 1's "Refutation condition" column — the column that carries the paper's central epistemic claim — is sliced off mid-word at the page edge. Readers see `Refutatio`, `Bias or`, `Silent bia`, `Era domi`.
3. **The paper reports no empirical result.** Section VI-D is a bulleted list in which five of six items end in the literal string *(TBD)*. IEEE Access has no registered-report track. A submission whose Results section defers its results is, to an AE, a protocol document.

Length is the *last* problem here, not the first. Adding five pages to a manuscript with clipped tables and placeholder figures produces an 18-page desk reject instead of a 13-page desk reject.

**The correct order of work is: (A) fix the production defects — roughly 6 hours, purely mechanical, and it is the highest-return work in this entire document; (B) resolve the empirical-results question, which is a strategic decision, not an editing decision; (C) then, and only then, expand to 18–20 pages.**

I have organised the report in the eleven parts requested, but Part 11 re-sequences everything by priority. If you read only two sections, read §1 (page-by-page) and §11 (action list).

---

## 0.1 Measured baseline — the facts this review is built on

Everything below is measured from the actual files, not estimated. These numbers are the substrate for every recommendation in this report.

**Page geometry** (probed directly from `ieeeaccess.cls`):

| Quantity | Value | Inches |
|---|---|---|
| `\textwidth` (two-column span) | 505.12 pt | 6.99 in |
| `\columnwidth` (single column) | 242.67 pt | 3.36 in |
| `\columnsep` | 19.70 pt | 0.27 in |
| `\textheight` | 672.00 pt | 9.30 in |

**IEEE Access official graphics spec** (from the IEEE Author Center): single-column art **3.5 in / 21 picas**, page-width art **7.16 in / 43 picas**; ≥1050 px wide for column art, ≥2150 px for page art; >300 dpi colour/greyscale, >600 dpi line art.

**Your figure files** (`docs/07_Paper/figs/`, read from the PNG `IHDR`/`pHYs` chunks):

| File | Pixels | dpi | Natural width | Overflow past `\textwidth` |
|---|---|---|---|---|
| `fig_dag.png` | 2280×1320 | 300 | 7.60 in | **+44.13 pt (0.61 in)** |
| `fig_pipeline.png` | 2280×1380 | 300 | 7.60 in | **+44.13 pt** |
| `fig_design.png` | 2280×1020 | 300 | 7.60 in | **+44.13 pt** |
| `fig_lineage.png` | 2280×1560 | 300 | 7.60 in | **+44.13 pt** |
| `fig_g3_trace.png` | 2280×1320 | 300 | 7.60 in | **+44.13 pt** |
| `fig_d3.png` | 2880×1020 | 300 | 9.60 in | **+188.67 pt (2.61 in)** |
| `fig_placeholder.png` | 1423×723 | 200 | 7.12 in | **+9.08 pt** |

**Overfull `\hbox` warnings from the compile log**, mapped to source lines:

| Source line(s) | Object | Overflow |
|---|---|---|
| 249–263 | **Table 2** (differentiation) | **123.33 pt** |
| 155–167 | **Table 1** (RQs / refutation) | **89.33 pt** |
| 633 | **Fig. 5** (`fig_d3`) | **188.67 pt** |
| 295–315 | **Table 3** (notation) | 35.33 pt |
| 609–625 | **Table 6** (simulation validation) | 36.33 pt |
| 397–406 | **Table 4** (estimator comparison) | 27.33 pt |
| 338, 445, 579, 589, 678 | **Figs. 1, 2, 3, 4, 6** | 44.13 pt each |
| 708, 715 | **Figs. 7, 8** (placeholders) | 9.08 pt each |
| 358 | display equation (5) | 43.22 pt |

Thirteen distinct objects overflow. Not one figure in this paper fits the page.

**Content volume** (words, from the LaTeX source):

| Section | Words | Assessment |
|---|---|---|
| I. Introduction | 516 | Thin — IEEE Access norm 900–1,200 |
| II. Problem Statement / RQs | 384 | Thin |
| III. Related Work | 836 | **Severely thin for 13 references** |
| IV. Formal Model and Identifiability | 908 | Adequate, under-illustrated |
| V. Methodology | 869 | Thin for a 5-stage protocol |
| VI. Results | 1,201 | Nominally adequate; ~40% is *(TBD)* |
| VII. Discussion | **247** | **Unacceptable — this is the paper's payload** |
| VIII. Threats and Limitations | 444 | Good content, compressed |
| IX. Conclusion | **159** | **Unacceptable** |
| Appendices A–G | 1,122 | Fragmented across 7 micro-sections |
| **Body total (I–IX)** | **5,564** | |

IEEE Access articles typically run **8,000–15,000 words**. You are at 5,564 body words — roughly **40% of the low end of the normal band**. The 13→20 page gap is not a layout problem; it is a **5,000-word content deficit**.

**References: 13.** IEEE Access regular articles typically cite **30–60**. Thirteen is the single most visible "this is not a journal paper" signal in the document, and an AE sees it in four seconds by scrolling to the last page.

**Structural absences:** zero `algorithm` environments, zero `theorem`/`lemma`/`definition`/`proposition`/`remark` environments, no graphical abstract (IEEE Access wants 660×295 JPG <45 KB), no author photographs, and biographies containing the literal string `...`.

---

# PART 1 — PAGE-BY-PAGE LAYOUT REVIEW

Rendered at 150 dpi and inspected individually. Text-density figures are extracted character counts per page (a normal full IEEE Access text page is ≈5,800–6,200 characters).

### Page 1 — 4,314 chars — *Grade: C+*

**What is right.** Title is strong and does real work — it poses a question, names the method, and names the object. The abstract is a genuinely good piece of technical writing.

**What is wrong.**
- **The abstract is one 320-word block with no paragraph break.** It is a grey slab. IEEE Access abstracts are 150–250 words. Yours is 30% over and reads as a wall.
- **The abstract's last sentence is a confession.** "The empirical partition itself is not claimed here." You have told the AE, in the abstract, that the paper has no result. Whatever you decide about the empirical pass, this sentence must be re-framed to lead with what *is* delivered rather than what is not.
- **`\history{Date of publication xxxx 00, 0000...}` and `\doi{10.1109/ACCESS.2024.0000000}` are visible on the printed page.** So is `This work was supported in part by ....` — with the four-dot ellipsis. These appear in the rendered PDF, above the title and in the footnote. An AE reads this as an unfinished draft submitted by accident.
- **Only 8 index terms**, and they are alphabetical generic keywords. "Correlated errors, error correlation" is a near-duplicate pair wasting a slot.
- Introduction begins at ~65% down the page with a single `\PARstart` paragraph, then the page ends. Weak entry.

**Redesign plan.** Split the abstract into two paragraphs at "The design is gated in two stages." Cut to 240 words. Fill `\history`, `\doi`, `\tfootnote`. Replace "error correlation" with "algorithmic monoculture" and add "model lineage" and "pre-registration". Move the first Introduction paragraph up by trimming abstract length.

### Page 2 — 6,080 chars — *Grade: D — hard production failure*

- **Table 1 is clipped by the page trim.** Overfull by **89.33 pt**. The rightmost column, "Refutation condition," is amputated. The reader sees `Refutatio` / `Bias or` / `Silent bia` / `Era domi` / `Flat trend`. **This table is the falsifiability contract of the entire paper and it is unreadable.**
- The table's caption ("Research questions and refutation conditions") promises exactly the content that has been cut off. The gap between promise and delivery is the worst possible first impression.
- Section II is set as `\subsection{Main question}` / `\subsection{Sub-questions}` — **sentence case**, while Section V uses `\subsection{Study Population Construction}` — **Title Case**. The paper is internally inconsistent in heading capitalisation from page 2 onward.
- Section III opens with two sentences and immediately drops to `\paragraph`. There is **no `\subsection` layer in Related Work at all** — the document skips from level 1 to level 4, which the class renders as run-in italic `a:`, `b:`, `c:`, `d:`. It looks like an internal memo, not a journal section.

**Redesign plan.** Table 1 must become a **double-column table** (`table*`) with a fourth "Status" column and a wrapped `p{}` column spec — see §4. Re-cast Related Work with real `\subsection` headings.

### Page 3 — 6,095 chars — *Grade: D — hard production failure*

- **Table 2 is the worst overflow in the document: 123.33 pt.** Content is destroyed mid-word: `what models—cro`, `judge/temperature/prompt; TEE`, `reconstructs post-training data an`, `judges favor related generato`, `welfare argument given correlate`. The comparison against related work — the table that establishes novelty — is **illegible**.
- **Table 3 (Notation), 35.33 pt overflow.** Also clipped, though less catastrophically.
- Two clipped tables stacked in one column with body text squeezed to the left. Right column is 100% table from top to bottom. Severe column imbalance.
- The notation table arrives *before* several of the symbols it defines are used, and is not referenced from the text at the point of first symbol use.

**Redesign plan.** Table 2 → full-width `table*` at the top of page 3 with `p{}` columns. Table 3 → move to a single-column `table` but restructure as a two-panel notation block (see §4, T-N1).

### Page 4 — 5,179 chars — *Grade: C−*

- **Table 4 overflows by 27.33 pt** — the "Fam.-share bias on D2 (A)" column is clipped, showing `bias on D2` and `(A)` with values `−5.3pp (300` and `−28.0pp (40` truncated mid-parenthesis. **Numbers cut off mid-value is the single most damaging typographic failure possible in a statistics paper.**
- **Equation (5) overflows by 43.22 pt.** The Woodbury identity runs past the column.
- Section V opens at the very bottom of the right column with a two-line stub before the page break — an orphaned section opening.
- Right column has the text `spine; stages 1–3 are complete and reported here, and stage 4 (yes` — a visible collision artifact with the following float.

**Redesign plan.** Table 4 → `table*`. Break equation (5) across two lines with `\begin{split}` or `\resizebox`. Force Section V to start on page 5 with `\clearpage` discipline or float re-ordering.

### Page 5 — 2,888 chars — *Grade: F — 50% empty, and the figure is broken*

This is one of the two worst pages in the manuscript.

- **Fig. 1 (Causal DAG) consumes the entire top half of the page** — full 6.99 in width, overflowing to 7.60 in — and is **more than 40% empty canvas**. The nodes float in a sea of white with no bounding logic.
- **The diagram has hard internal collisions.** I cropped it at 150 dpi: arrow strokes pass *straight through* the "Release date (quarter)" node box; the annotation "Single causal attribution is impossible by construction..." **overlaps the "Error trait" node box**, with the words "Error trait" printed on top of the annotation text. Two separate text runs occupy the same pixels.
- The orange and red-dashed edges cross the black lineage edges at shallow angles with no crossing-gaps, producing visual knots.
- The remaining half-page is a bulleted list plus Table 5, which is a **tiny 2-column, 8-row check-mark table floating alone**. A "lonely table."
- Net: **2,888 characters — less than half a page of text.**

**Redesign plan.** This page needs total reconstruction:
1. **Redraw Fig. 1 as a single-column figure** at 3.5 in. A five-node DAG does not need 7 inches. Move the long annotation *out* of the canvas and into the caption. Add crossing-gaps on edges. Route the mediator edge orthogonally.
2. Fig. 1 moves to the **top of the left column on page 3**, adjacent to §III-A where the two-estimand rule is argued.
3. Table 5 (G3 inputs) gains three columns (see §4) and becomes a proper single-column table.
4. The reclaimed half-page absorbs the expanded §IV-D (identifiability conditions), currently 5 lines for 4 conditions.

### Page 6 — 2,950 chars — *Grade: F — 50% empty, and the figure is broken*

- **Fig. 2 (Protocol architecture) occupies the entire top half**, again full-width, again overflowing.
- **The figure is clipped on the left edge.** Because it is 7.60 in centred in a 6.99 in box, it hangs 0.30 in off *each* side. Box 1's title renders as `...ulation audit`; its body renders as `...pen-weight models`, `...ies x 14 quarters`, `...ed subset (crossed)`, `...ed lineage edges`. **The first stage of your five-stage protocol has its label cut in half.**
- Boxes 3, 4 and 5 collide: the arrow leaving "3. Pre-analysis design (G3)" overlaps the left border of "4. Measurement + decomposition."
- Enormous vertical dead space between the box row and the caption band.
- Again **2,950 characters** of actual text.

**Redesign plan.** Fig. 2 is a legitimate double-column figure — a 5-stage horizontal pipeline earns the width. But: export at exactly **6.99 in**, reduce height by 35%, fix the box collisions, and move the "The ordering is the contribution…" sentence from the canvas into the caption. Reclaimed space absorbs Algorithm 1 (see §10).

### Page 7 — 5,736 chars — *Grade: F — text and table physically overlap*

**This is the worst page in the document.**

- Table 6 (left, single-column, +36.33 pt overflow) and Table 7 (right) sit at the top. Table 6's overflow drives its right-hand columns **into the right column's body text**. At 150 dpi I can read three separate collisions:
  - Table 6's `path decides` prints **on top of** the body text `era shares in the same order of magnitude...`
  - Table 6's `documented` prints **on top of** `The winner keeps all six families...`
  - Table 6's Verdict column (`GO`/`GO`/`GO`/`n/a`/`n/a`) sits **over** the running text of the right column.
- This is not a tight fit. This is **two text runs rendered in the same physical space.** It is the defect a Production Editor is specifically employed to catch, and it survives into the committed PDF.
- Table 6's footnote is set in a smaller size than IEEE Access table notes and uses `*` where IEEE house style uses superscript lowercase letters.
- Section VI-D "Empirical outputs (pending measurement)" begins here — a six-item bullet list, five items ending in *(TBD)*.

**Redesign plan.** Table 6 → **full-width `table*`** at the top of page 7 with a `p{}` recovery column; Table 7 stays single-column and moves to page 8. The *(TBD)* list is addressed in §6 and §11 — it cannot stay in this form.

### Page 8 — 3,559 chars — *Grade: D+*

- Fig. 3 (design heatmap) takes the **entire top 40%** at full width, overflowing 44.13 pt.
- The heatmap is a **6×14 grid of integers, most of them "1"**. It is displaying 47 numbers — 39 of which are the digit 1 — using 40% of a page. The colour bar is calibrated 0.0–3.0 for data that is almost entirely {0,1,2}. This is the lowest information-density object in the paper.
- Quarter labels are rotated 45° and set in a sans-serif face that matches nothing else in the document.
- Below it, §VIII "Threats to Validity" is a nine-item bullet list running to the page bottom — a dense grey block immediately under a near-empty graphic. Worst possible visual rhythm.

**Redesign plan.** **Fig. 3 becomes a single-column figure** (3.5 in). Drop the numeric annotations from cells with value 1 — encode by colour only, annotate only cells ≥2. Recalibrate the colour bar to a 3-step discrete scale. This halves its area and doubles its readability. The reclaimed space takes the expanded §VIII prose (see §6).

### Page 9 — 2,558 chars — *Grade: F — lowest text density of any content page*

- Fig. 4 (lineage) is the **tallest figure in the paper** (2280×1560 px = 7.60×5.20 in) and takes **55% of the page** at full width.
- It plots **five edges**. Five parent–offspring relationships, plus one chain, occupy over half a page.
- The marker labels (`L1`, `1.5`, `3.2`, `7B`, `8x22B`, `Mixtral`, `Small`, `S1`, `4.6v`, `3m`) are set at ~5 pt and are unreadable at print size. Several overlap their markers.
- Legend entries ("gated access", "public access", "verified lineage edge", "documented within-family chain", "cross-family teacher leakage") float in the plot area over data.
- Grey annotations `Gemini-3 (closed)` and `GPT-4o (closed)` are set in a lighter grey than the caption text and will drop out in print.
- §IX Conclusion starts at the bottom of the right column: **159 words.**

**Redesign plan.** Fig. 4 → **single-column**, or better: **merge Figs. 3 and 4 into one two-panel double-column figure** (panel (a) occupancy, panel (b) lineage overlay) — they share the same family × quarter axes and currently duplicate that grid twice, ten pages apart. This saves ~0.6 page and makes the relationship visible instead of implied.

### Page 10 — 3,535 chars — *Grade: D*

- **Fig. 5 (D3 detection) is clipped on both edges** — overflow **188.67 pt (2.61 in)**, by far the worst. The title renders as `D3 (nested design): aliasing must be detected, never silently "succeed" -- 300 reps/scenario` with characters lost at the right trim.
- The figure uses a **9.60 in canvas to display four numbers**: 100%, 100%, 100%, 100%. Two bar panels, each with two bars, all at ceiling. There is no variance to see. **This is a table pretending to be a figure**, and it is the clearest single example of the density problem in this manuscript.
- The subtitle text `silent CI coverage (undetected reps): 0 total, 0 covered` is set below the axes in a colour that reads as an axis label.
- Appendices A–D begin on this page as four separate `\section` blocks of 70, 151, 111 and 110 words. **Four micro-appendices averaging 110 words each.** This reads as fragmentation, not thoroughness.

**Redesign plan.** **Delete Fig. 5 and replace it with a 4-row table** (see §4, T-N2) occupying one-fifth the space. Merge Appendices A–D into two substantive appendices (see §5).

### Page 11 — 2,915 chars — *Grade: F — figure clipped on both sides*

- **Fig. 6 (G3 decision trace) is clipped at both trims.** The title begins mid-word: `e: era-share bias at the 1000-rep confirmation (and 2000-rep robustness); o = B, ^ = A, s` — the words before `e:` and after `s` are gone. The reader cannot determine what the figure is titled.
- **Internal label collisions**, confirmed at 150 dpi: `n0=21` and `winner` are printed on top of each other, rendering as `n0=2⅟nner`. Below them, `FAIL` and `PASS` overprint as `FAILPASS`. The legend `confirmation band (|bias| ≤ 4.0pp)` overprints the annotation `baseline`.
- This is the figure that justifies the paper's headline claim — 22 of 47 models, 67% cost reduction. **It is unreadable and mislabelled.**
- Below it, Appendices E, F, G in three columns of dense small text with no visual relief.

**Redesign plan.** Regenerate Fig. 6 at **3.5 in single-column**, move the title into the caption entirely (IEEE style: figures do not carry internal titles), de-conflict the vertical annotations with `matplotlib` `annotate(..., xytext=)` offsets, and move the legend outside the axes.

### Page 12 — 985 chars — *Grade: F — automatic desk rejection*

**985 characters. One-sixth of a page of text.** The rest is two full-width boxes reading:

> **FIGURE PLACEHOLDER**
> Final figure to be added by the authors
> *See the caption above for the intended content.*

Each is 6.99 in wide and ~2.5 in tall. Together they consume 83% of the page.

There is no version of this that survives contact with an editor. A placeholder figure in a submitted PDF is treated as an incomplete submission, full stop.

**Redesign plan.** Non-negotiable: either produce the real figures, or **delete both figures and the section that references them**, converting §VI-D into a short forward-looking paragraph in §VII. See §11-C for the strategic options.

### Page 13 — 4,530 chars — *Grade: C−*

- Tables 8 and 9 are stacked in the left column — 22 rows and 22 rows. **Two long roster tables in the same column, one after the other, listing largely the same 22 models.** They should be one table with an extra column.
- The reference list runs 13 items in the right column and stops. On the last page of an IEEE Access paper, a 13-item reference list is conspicuous.
- **Both biographies contain the literal text `His research interests include ... .`** with a visible four-dot ellipsis. Both lack photographs (`IEEEbiographynophoto`).
- Both biographies use "His" — verify this is correct for both authors before submission; if not, correct it.
- Table 8's "Est. min." column sums to 710 and 2,154 in a row visually indistinguishable from data rows.

**Redesign plan.** Merge Tables 8 and 9 into one full-width `table*` (see §4). Expand references to 35+. Write real biographies and supply photographs.

### Page-density summary

| Page | Chars | % of full page | Verdict |
|---|---|---|---|
| 1 | 4,314 | 71% | Title page — acceptable |
| 2 | 6,080 | 100% | Full but **table clipped** |
| 3 | 6,095 | 100% | Full but **two tables clipped** |
| 4 | 5,179 | 85% | **Table + equation clipped** |
| 5 | 2,888 | **47%** | **Half empty** |
| 6 | 2,950 | **48%** | **Half empty** |
| 7 | 5,736 | 94% | **Text/table overlap** |
| 8 | 3,559 | 58% | Under-filled |
| 9 | 2,558 | **42%** | **Worst content page** |
| 10 | 3,535 | 58% | Under-filled |
| 11 | 2,915 | **48%** | **Half empty** |
| 12 | **985** | **16%** | **Placeholders** |
| 13 | 4,530 | 74% | Back matter |

**Six of thirteen pages are below 60% text density.** The paper is not 13 pages of content — it is approximately **9.5 pages of content spread across 13 pages by oversized figures**. This is why it feels thin: not because 13 is a small number, but because a third of the paper is white space and broken graphics.

---

# PART 2 — FIGURE PLACEMENT REVIEW

## 2.1 Root cause — why every figure is full-width

This is a single-line bug, repeated eight times, and it explains the entire layout problem.

The IEEE Access class defines `\Figure` at `ieeeaccess.cls:427` as:

```latex
\def\@@@Figure[#1](#2)[#3]#4#5{%
      \setbox\figbox\hbox{\includegraphics[#3]{#4}}%
      \ifdim\wd\figbox<\columnwidth% Columnwidth Figure
        \begin{figure}[#1]...
      \else% Wide Figure
        \begin{figure*}[#1]...
```

The macro chooses single- vs double-column **by measuring the graphic's natural width**, and the third optional argument `[#3]` — the `\includegraphics` key list — **defaults to `[scale=1]`**.

Every call in `manuscript.tex` omits `[#3]`:

```latex
\Figure[t!](topskip=0pt, botskip=0pt, midskip=0pt){figs/fig_dag.png}{...}
```

So every figure is measured at its natural 300 dpi size — 7.60 in — which exceeds `\columnwidth` (3.36 in), so **every figure is forced into `figure*`**, and then typeset at 7.60 in inside a 6.99 in box, hanging 0.30 in off each trim.

**The fix is to supply the graphics options argument.** Two forms:

```latex
% Double-column figure — fills the text block exactly, no overflow
\Figure[t!](topskip=0pt, botskip=0pt, midskip=0pt)[width=\textwidth]{figs/fig_pipeline.png}{...}

% Single-column figure — note 0.99, see the trap below
\Figure[t!](topskip=0pt, botskip=0pt, midskip=0pt)[width=0.99\columnwidth]{figs/fig_dag.png}{...}
```

> **Trap — read this twice.** The class tests `\ifdim\wd\figbox<\columnwidth`, a **strict** inequality. If you write `width=\columnwidth`, the box is *equal to*, not *less than*, `\columnwidth`, the test fails, and **the figure still goes double-column** — while now being half the width it should be, leaving a 3.5 in blank gap beside it. You must use `width=0.99\columnwidth` (or any value strictly below). This will cost you an afternoon if you don't know it.

Fixing this one argument across eight call sites removes **all 8 figure overflow warnings** and is the highest value-per-minute edit available to you.

## 2.2 Per-figure verdicts

### Fig. 1 — Causal DAG → **SINGLE-COLUMN, left column, page 3**

**Verdict: single-column, 3.5 in × 2.6 in.**

A DAG with five nodes and six edges does not need 7 inches. At full width it is 40% empty canvas. Compressed to 3.5 in with the long annotation moved to the caption, it becomes a dense, readable schematic.

**It must also be redrawn**, not merely resized — the current version has arrow strokes passing through node boxes and the annotation block overprinting the "Error trait" node.

**Placement:** top of the **left** column, page 3, immediately adjacent to §IV-A "Setup and notation," where the mediator/confounder argument is made. It currently sits on page 5, two pages after the text that needs it.

### Fig. 2 — Protocol architecture → **DOUBLE-COLUMN, keep, but rebuild**

**Verdict: double-column, 6.99 in × 2.3 in (currently 4.6 in tall — halve it).**

This is the one figure that legitimately earns full width: a five-stage horizontal pipeline with three gate annotations is genuinely wide. Keep it double-column.

**But:** export at exactly 6.99 in, cut the height by ~50% (the current version is mostly vertical dead space), fix the box-3/box-4 collision, and move the "The ordering is the contribution…" sentence into the caption — figures should not carry paragraph-length internal prose.

**Placement:** top of page 5, opening §V Methodology. This is the paper's roadmap figure and should be the first thing a reader sees in the Methodology section.

### Fig. 3 — Design heatmap → **SINGLE-COLUMN**

**Verdict: single-column, 3.5 in × 2.2 in — or merge with Fig. 4 (preferred).**

A 6×14 grid of small integers is a compact object. At 7.6 in it is displaying 47 numbers, 39 of which are "1," across 40% of a page.

**Preferred option:** merge with Fig. 4 into a single double-column two-panel figure (see below). **Fallback:** single-column, with cell annotations dropped for value-1 cells and the colour bar reduced to a 3-step discrete legend.

### Fig. 4 — Verified lineage → **MERGE WITH FIG. 3 into a double-column two-panel figure**

**Verdict: merge. New Fig. 3(a)+(b), double-column, 6.99 in × 2.8 in.**

Figs. 3 and 4 **plot the same axes twice** — family (6 rows) × release quarter (14 columns) — separated by one page. Fig. 3 shows occupancy; Fig. 4 shows the same grid with lineage edges overlaid. Presenting them as two full-width figures wastes ~0.9 page and, worse, **hides the relationship**: the reader must hold the occupancy pattern in memory while looking at the lineage plot.

As a two-panel figure — (a) occupancy heatmap, (b) same grid with the five verified edges and the teacher-leakage arrows — the reader sees *"the design is crossed, and here is the lineage structure inside it"* in one glance. This is the paper's central design claim, and it should be one figure.

Additionally, the 5 pt marker labels must go to ≥7 pt and the legend must move outside the axes.

### Fig. 5 — D3 detection bars → **DELETE; CONVERT TO TABLE**

**Verdict: remove from the paper entirely.**

Four bars, all at exactly 100%, plus a line of text reporting "0 total, 0 covered." **This figure communicates four numbers, all of which are the same number.** It occupies 9.6 inches of width — the largest canvas in the paper — to say "the detectors fired every time."

Replace with a 4-row × 4-column table (T-N2 in §4) that additionally reports the per-detector statistics currently buried in Appendix C prose. The table will occupy roughly one-fifth the area and carry three times the information.

Reviewer #1 will notice that a figure with no variance is a figure with no content, and will treat it as padding — the exact accusation you are trying to avoid.

### Fig. 6 — G3 decision trace → **SINGLE-COLUMN, right column, page 8**

**Verdict: single-column, 3.5 in × 2.8 in — and regenerate from scratch.**

The current version is clipped at both trims, has three separate label-overprint collisions (`n0=21`/`winner`, `FAIL`/`PASS`, legend over `baseline`), and carries an internal title that IEEE style forbids.

This figure supports the paper's most quotable claim — 22 of 47 models, 67% cost reduction — and it is currently the *least* legible object in the document.

Regenerate with: no internal title (caption only), legend outside the axes via `bbox_to_anchor`, vertical annotations staggered with alternating `xytext` y-offsets, serif font family to match the body text, and a marked winner point at n=22.

### Figs. 7 and 8 — Placeholders → **DELETE**

**Verdict: remove.** See §11-C for the three strategic options. Under every one of them, a box reading "FIGURE PLACEHOLDER" does not appear in a submitted PDF.

## 2.3 Resulting figure budget

| Figure | Current | Recommended | Width | Page |
|---|---|---|---|---|
| DAG | 2-col, broken | **1-col** | 3.5 in | 3 (left) |
| Protocol architecture | 2-col, clipped | **2-col, rebuilt** | 6.99 in | 5 (top) |
| Occupancy + lineage | two 2-col figs | **one 2-col, 2-panel** | 6.99 in | 7 (top) |
| D3 detection | 2-col | **deleted → table** | — | — |
| G3 trace | 2-col, broken | **1-col** | 3.5 in | 8 (right) |
| Placeholders ×2 | 2-col | **deleted** | — | — |

**Space reclaimed: approximately 2.6 pages.** That is 2.6 pages of white space and broken graphics converted back into usable area — which is precisely the room the new content in Part 3 and Part 6 needs.

---

# PART 3 — TWELVE NEW FIGURES

Each is specified so it can be handed to a figure-generation script without further design decisions. Placement assumes the reflow in §2.3.

### NF-1 — Estimator geometry: why the crossed design is identifiable
- **Purpose:** Give the reader the *intuition* behind rank-deficiency before the algebra. Two side-by-side schematics of the incidence matrix **C** = [**Z**_F **Z**_E]: (a) crossed design — column spaces intersect only at the intercept, full rank; (b) nested design — family columns lie inside era columns, rank-deficient, σ²_L and σ²_E perfectly aliased.
- **Location:** §IV-D, page 4, right column.
- **Width:** single-column, 3.5 × 2.4 in.
- **Caption:** *Geometric intuition for identifiability. In a crossed design (a), the family and era column spaces of the incidence matrix intersect only in the intercept, so the variance components are separately estimable. Under nesting (b), each family occupies a single era; the family columns lie within the era span and σ²_L, σ²_E are perfectly aliased. Appendix D proves the crossing condition of Section IV-D is sufficient for full column rank.*
- **Why it matters:** This is the single most valuable addition in the list. Right now, identifiability is asserted in five lines of text and proved in a 110-word appendix. A reader cannot *see* it. Reviewer #1 will ask for exactly this.

### NF-2 — Two-estimand decision diagram
- **Purpose:** θ_P vs θ_M is the paper's most novel conceptual move and currently lives in a 10-line subsection with no visual. Show the split: observational path (family grouping, era conditional) → θ_P; mechanistic path (co-released cohorts + verified fine-tune edges, era held exactly fixed) → θ_M; with the data requirements and the sample size available to each (47/22 vs 5 edges).
- **Location:** §IV-C, page 4.
- **Width:** single-column, 3.5 × 2.6 in.
- **Caption:** *The two-estimand rule. The observational estimand θ_P conditions on era and uses the verified family grouping across the full connected subset; the mechanistic estimand θ_M holds era exactly fixed on co-released cohorts and verified parent–offspring edges. The two answer different questions and are reported separately throughout; neither is a fallback for the other.*

### NF-3 — REML optimisation and Woodbury computation pipeline
- **Purpose:** Appendix E ("REML and Woodbury Computation") is **95 words** — the shortest appendix in the paper — for what is the computational core of the method. A flow diagram earns its space: log-variance parameterisation → PSD clip → Woodbury inversion (20×20 instead of N×N) → numerically differentiated Hessian → Monte-Carlo share CIs.
- **Location:** Appendix E, page 11.
- **Width:** double-column, 6.99 × 1.9 in (horizontal flow).
- **Caption:** *REML evaluation path. Reparameterising to log-variances keeps the optimiser unconstrained; the Woodbury identity (5) reduces each likelihood evaluation from an N×N solve to a (F+E)×(F+E) = 20×20 solve, making the per-evaluation cost O(N) with negligible constants. Share confidence intervals combine a numerically differentiated Hessian with a Monte-Carlo delta step.*

### NF-4 — Error decomposition: what σ²_L, σ²_E, σ²_U mean on one item
- **Purpose:** A "running example" figure. Take one MMLU item and one 6-model slice; show the observed per-model residual decomposed into family offset + era offset + model-unique remainder, as a stacked bar per model. This makes the abstract partition concrete in a way no equation can.
- **Location:** §IV-A, page 3 or 4.
- **Width:** single-column, 3.5 × 2.5 in.
- **Caption:** *Worked decomposition on a single benchmark item. Each model's error residual is expressed as the sum of its family effect α, its era effect β, and a model-specific remainder u. The variance partition of Section IV-C is the population-level version of this per-model split.*

### NF-5 — Study population construction: 47 → 22 attrition waterfall
- **Purpose:** The 47→22 reduction is stated as a number and justified in prose. A waterfall showing each exclusion reason with counts (era-window, structural identifiability, statistical recoverability, redundant in-cell replication) makes the gate auditable at a glance.
- **Location:** §V-C or §VI-C.
- **Width:** single-column, 3.5 × 2.4 in.
- **Caption:** *Construction of the minimum valid population. Beginning from the 47-model connected subset, each model is retained under exactly one binding reason or dropped as redundant in-cell replication. The 22-model result is the smallest population that remains structurally identifiable and clears the simulation-based recoverability bar (Table 7).*

### NF-6 — Simulation design battery (D1/D2/D3) schematic
- **Purpose:** The three simulation regimes are described in prose and summarised in a clipped table. Show them: D1 balanced 6×14 grid, D2 real occupancy grid, D3 nested grid — three miniature occupancy matrices side by side with their expected verdicts.
- **Location:** §V-B, page 5.
- **Width:** single-column, 3.5 × 1.8 in.
- **Caption:** *The three simulation regimes. D1 is a balanced crossed reference; D2 copies the real occupancy of the study population; D3 is nested by construction and must fail detectably. A design that "succeeds" under D3 has a broken detector, not a valid estimate.*

### NF-7 — Recoverability frontier: bias and coverage vs population size
- **Purpose:** Fig. 6 shows era-share bias at three population sizes. Extend it into a proper frontier: bias (left axis) and CI coverage (right axis) as continuous functions of n over the full sweep, with the confirmation band and the chosen n = 22 marked. This converts a three-point scatter into an actual result.
- **Location:** §VI-C, page 8.
- **Width:** single-column, 3.5 × 2.6 in.
- **Caption:** *Recoverability frontier. Era-share bias and confidence-interval coverage across candidate population sizes at 1,000 repetitions, with the pre-registered confirmation band (|bias| ≤ 4.0 pp, coverage ≥ 90%) shaded. n = 22 is the smallest size clearing both criteria; n = 21 fails the bias criterion by 0.9 pp.*

### NF-8 — Sensitivity-analysis workflow
- **Purpose:** §VI-D lists five sensitivity blocks in a bullet with no structure. A diagram showing each perturbation (leave-one-family, leaked-drop, subject-drop, trait-definition, leaderboard cross-check), what it perturbs, and which claim it stresses.
- **Location:** §VIII, page 9.
- **Width:** double-column, 6.99 × 1.7 in.
- **Caption:** *Pre-registered sensitivity battery. Each block perturbs one input and re-runs the full partition; the affected claim and the pre-registered tolerance are fixed before measurement. A block that moves the lineage/era ordering, not merely the magnitudes, is a refutation under RQ6.*

### NF-9 — Threat model / failure-mode map
- **Purpose:** §VIII is nine bullets of genuinely good self-criticism, presented as an undifferentiated list. A 2×2 map — axes *detectable by the design* × *bounded in magnitude* — placing each of the nine threats, with the mitigations attached.
- **Location:** §VIII, page 9.
- **Width:** single-column, 3.5 × 3.0 in.
- **Caption:** *Threat map. Nine identified threats positioned by whether the design detects them (D3 battery, identifiability audit) and whether their magnitude is bounded by a reported quantity. Threats in the lower-left quadrant — visibility bias and off-subset scope — are carried as scope restrictions rather than mitigated.*

### NF-10 — Decision rule for RQ6
- **Purpose:** The RQ6 decision rule (dominant era share refutes diversification; dominant lineage share is necessary but not sufficient) is asymmetric and easily misread. A decision tree removes the ambiguity and makes the pre-registration concrete.
- **Location:** §VII Discussion, page 9.
- **Width:** single-column, 3.5 × 2.4 in.
- **Caption:** *Pre-registered decision rule for RQ6. The rule is deliberately asymmetric: a dominant era share refutes cross-family diversification as a remedy on the connected subset, whereas a dominant lineage share is a necessary but not sufficient condition for recommending it, because the connected subset may not represent the broader model population.*

### NF-11 — Reproducibility and artifact workflow
- **Purpose:** The project has substantial real infrastructure (`src/lineage_era/`, 25+ modules, staged artifacts, a GPU runbook). None of it is visible in the paper. A workflow figure from metadata ingestion → population file → simulation → G3 optimiser → eval pass → decomposition → artifacts, annotated with the actual module names and output files.
- **Location:** Appendix F, page 11.
- **Width:** double-column, 6.99 × 2.0 in.
- **Caption:** *Reproducibility path. Every stage reads a versioned input and writes a versioned artifact; the released code reproduces all Phase 0 and Phase 1 numbers in this paper from the recorded seeds on CPU alone. Phase 2 additionally requires the GPU budget of Table 8.*
- **Why it matters:** IEEE Access reviewers weight reproducibility heavily, and you have a genuinely strong story here that the manuscript currently does not tell.

### NF-12 — Deployment implication: co-failure ceiling under each regime
- **Purpose:** §VII is 247 words and ends without showing the reader what the answer would *look like*. Plot the ensemble co-failure probability as a function of ensemble size under a lineage-dominant regime vs an era-dominant regime. This is the practitioner payoff and it is currently invisible.
- **Location:** §VII, page 9 or 10.
- **Width:** single-column, 3.5 × 2.5 in.
- **Caption:** *Operational consequence of the partition. Under a lineage-dominant regime, adding cross-family members drives the joint all-wrong rate down; under an era-dominant regime the curve flattens and diversification buys little. The measured shares select between these regimes, which is why the partition — not the pairwise correlation — is the decision-relevant quantity.*

**Figure budget after Part 2 and Part 3:** 4 retained/rebuilt + 12 new = **16 figures**, of which 12 single-column and 4 double-column. That is the correct ratio for IEEE Access — see §8.

---

# PART 4 — TABLE REVIEW

## 4.1 Existing tables

### Table 1 — Research questions and refutation conditions
**Overflow: 89.33 pt. Clipped at trim.**
**Action: convert to `table*` (double-column), add a Status column.**

The current 4-column single-column layout cannot hold this content. As a full-width table with `p{}` columns it becomes readable and gains room for a fifth column that answers the question every reviewer will ask: *which of these has actually been executed?*

```latex
\begin{table*}[t]
\caption{\textbf{Research questions, operating data, refutation conditions, and execution status.}}
\label{tab:rq}
\centering\small
\begin{tabular}{@{}l p{0.30\textwidth} l p{0.26\textwidth} l@{}}
\hline
RQ & Question & Operates on & Refutation condition & Status \\
\hline
...
\end{tabular}
\end{table*}
```

### Table 2 — Differentiation against closest related work
**Overflow: 123.33 pt — the worst in the document. Content destroyed mid-word.**
**Action: convert to `table*`, restructure to 5 columns.**

Current columns (Work / Object / What it does) are too coarse. Split into: Work · Object of study · Method · What it establishes · **What it leaves open**. That last column is where your novelty claim lives, and it currently does not exist as a column at all — it is implied. Make it explicit; an AE scanning for novelty will read exactly that column.

Add a footnote defining "connected subset" on first table use — the term appears in the table before it is defined in the text.

### Table 3 — Notation
**Overflow: 35.33 pt.**
**Action: keep single-column, restructure into two grouped panels.**

Currently a flat 14-row symbol list. Regroup into **(a) Design and population** (N, i, f(i), e(i), F, E) and **(b) Model and estimands** (Y, μ, α, β, u, σ², θ_P, θ_M, C, V, ℓ_R, VIF) with a horizontal rule and small italic panel labels. Same information, half the scanning cost.

Reduce the "Meaning" column to `p{0.55\columnwidth}` and set in `\footnotesize` to eliminate the overflow.

### Table 4 — Estimator comparison
**Overflow: 27.33 pt. Numeric values clipped mid-parenthesis.**
**Action: convert to `table*`, add two columns.**

This is a good table doing important work — it is the evidence that the direct maximiser beats `statsmodels`' crossed-variance path. But it clips exactly where the numbers are, which is fatal.

As a `table*` it has room for the two columns it needs: **log-likelihood at optimum** and **wall-clock per fit**. Reviewer #1 will ask "is the difference statistically or numerically meaningful?" and the log-likelihood column answers it directly.

### Table 5 — G3 optimisation inputs
**Action: keep single-column, expand from 2 to 4 columns.**

Currently 7 rows × 2 columns of check marks and crosses. It is a "lonely table" — visually trivial, floating in white space on page 5.

Add: **Source** (where the input comes from), **Outcome-independent?** (the property that makes G3 valid). The third column converts a trivial checklist into the table that *proves* the outcome-independence claim — which is one of the paper's two main contributions and is currently supported only by assertion.

### Table 6 — Simulation validation (Phase 1)
**Overflow: 36.33 pt, and it physically overlaps the adjacent column's body text.**
**Action: convert to `table*`. Highest-priority table fix after Tables 1 and 2.**

Also: replace the `*` footnote marker with IEEE house style (superscript lowercase letter), and add a **repetitions** column — the text mentions 300 reps for D1 and D2 but the table does not carry it, forcing the reader back into prose for a number that belongs in the table.

### Table 7 — G3 gate
**Action: keep single-column, move to page 8, add a column.**

Structurally the cleanest table in the paper. Add a **Δ cost (%)** column so the 67% reduction claim appears in the table that establishes it rather than only in prose.

### Tables 8 and 9 — GPU cost plan / population roster
**Action: merge into one full-width `table*`.**

These list overlapping model sets (Table 8: all 47 with cost; Table 9: the 22 kept with reason) stacked in the same column on page 13. Merge into a single 47-row `table*` with columns: Family · Model · Quarter · Params · Access · Est. GPU-min · **In population?** · **Binding reason**. One table, complete, auditable, and it eliminates the model-name duplication that currently spans two tables.

## 4.2 Six new tables

### T-N1 — Notation, grouped (replaces Table 3)
Two-panel restructure as described above. Single-column.

### T-N2 — D3 detector battery results (replaces Fig. 5)
| Detector | Statistic | Threshold | Flagged (of 300) | Silent CI coverage |
|---|---|---|---|---|
| BLUP collinearity | \|corr(û_F, û_E)\| | > 0.9 | 300 (100%) | 0 |
| SE inflation | ŜE ≥ \|θ̂\| | ratio ≥ 1 | 300 (100%) | 0 |
| Profile flatness | log-variance drop | < 1.92 | 300 (100%) | 0 |
| Non-convergence | optimiser status | — | (report) | 0 |

**Purpose:** Replaces a figure that displays four identical numbers with a table that displays the detector definitions, thresholds, and results together. Also surfaces the Appendix C thresholds (0.9, 1.92) into the main body where a reviewer will look for them.
**Location:** §VI-B, page 6. Single-column.
**Note required:** *A design passes the gate only if all three detectors flag the aliasing in ≥90% of repetitions and no repetition shows silent CI coverage.*

### T-N3 — Computational complexity and cost
| Stage | Complexity | Dominant term | Measured cost | Hardware |
|---|---|---|---|---|
| Occupancy audit | O(N) | metadata fetch | — | CPU |
| REML fit (one) | O(N·(F+E)²) | Woodbury solve, 20×20 | — | CPU |
| Bootstrap (B reps) | O(B·N·(F+E)²) | — | — | CPU |
| G3 optimiser sweep | O(\|S\|·R·N) | simulation reps | — | CPU |
| Phase 2 eval pass | O(N·items·5) | forward passes | 710 GPU-min | 8×H200 |

**Purpose:** IEEE Access reviewers routinely ask for a complexity table in a methods paper. You have all these numbers scattered across Appendices E and F; consolidating them is nearly free and directly answers a standard reviewer request.
**Location:** Appendix F or §V-E. Single-column.

### T-N4 — Reproducibility checklist
| Item | Status | Location |
|---|---|---|
| Population file (47 models, verified metadata) | Released | `datasets/` |
| Lineage edge record with provenance | Released | `datasets/` |
| Simulation seeds (D1/D2/D3) | Released | `src/results/phase1/` |
| Estimator implementation | Released | `src/lineage_era/estimator.py` |
| Estimator cross-validation vs ANOVA/statsmodels | Released | `src/lineage_era/analysis/reml.py` |
| G3 optimiser and decision trace | Released | `src/lineage_era/phase2_population_optimizer.py` |
| Pre-registration document (frozen before eval) | — | — |
| Phase 2 eval outputs | Pending | — |

**Purpose:** You have a genuinely strong reproducibility story that the paper never tells. This table tells it in 20 lines. It also handles the *(TBD)* problem honestly by putting the pending items in a structured place rather than leaving them as bullets in the Results section.
**Location:** Appendix F, page 11. Single-column.

### T-N5 — Prior estimates of model error correlation
| Study | Population | Measure | Reported value | Comparable to θ_P? |
|---|---|---|---|---|
| Kim et al. 2025 | 350+ models, 2 leaderboards | pairwise agreement among co-erring | ≈60% | No — cross-sectional |
| Chen 2026 | 67 frontier models | joint all-wrong rate | ≈2× pairwise implies | No — no partition |
| Kuai et al. 2026 | open-weight subset | behavioural entanglement | — | Partially |
| Messing 2026 | eval pipelines | measurement-error variance | — | No — different variance |
| This work | 22/47 connected subset | σ²_L / σ²_E / σ²_U shares | pending | — |

**Purpose:** Related Work currently argues differentiation in prose. This table makes the incommensurability of prior measurements *visible*, which is a much stronger novelty argument than a paragraph. It also gives the expanded Related Work section (§6) a spine.
**Location:** §III, page 3. Double-column (`table*`).

### T-N6 — Sensitivity battery specification
| Block | Perturbation | Claim stressed | Pre-registered tolerance |
|---|---|---|---|
| Leave-one-family | drop each family in turn | family-share stability | ordering preserved |
| Leaked-drop | drop documented teacher-leaked models | era-channel purity | \|Δ era share\| ≤ ... |
| Subject-drop | drop each MMLU subject group | trait robustness | ordering preserved |
| Trait definition | binary vs continuous per-model trait | LPM/REML choice | ordering preserved |
| Leaderboard cross-check | compare to public leaderboard accuracy | sanity, not validation | correlation ≥ ... |

**Purpose:** Converts a bullet list into a pre-registration artifact. The "pre-registered tolerance" column is what makes this a *design* rather than a *plan*, and it is currently absent.
**Location:** §VIII or Appendix. Single-column.

**Table budget:** 9 existing (2 merged → 8) + 6 new = **13 tables**, of which 5 double-column.

---

# PART 5 — SECTION HEADING REVIEW

## 5.1 Systemic problems

**(a) Capitalisation is internally inconsistent.** §II uses sentence case (`Main question`, `Sub-questions`, `The two-estimand rule`); §V uses Title Case (`Study Population Construction`, `Trait Measurement and Decomposition`); §VI mixes both (`Population Audit` but `Empirical outputs (pending measurement)`). IEEE Access uses Title Case for `\subsection`. **Fix all 15 subsection headings to Title Case.** A copy editor will flag every one of these.

**(b) Related Work skips two heading levels.** §III goes directly from `\section` to `\paragraph`, producing run-in italic headings rendered `a:`, `b:`, `c:`, `d:`. This is the class's *fourth*-level heading being used as a second-level structure. It reads as an internal document.

**(c) Seven appendices averaging 160 words each.** Appendices A (70 words), B (151), C (111), D (110), E (95) are micro-sections. Fragmentation reads as an unfinished outline, not as thoroughness.

**(d) One heading openly admits incompleteness.** `Empirical outputs (pending measurement)` — see §11-C.

## 5.2 Heading-by-heading rewrites

| # | Current | Recommended |
|---|---|---|
| I | Introduction | **Introduction** *(keep)* |
| II | Problem Statement and Research Questions | **Problem Formulation and Research Questions** |
| II-A | Main question | **Primary Research Question** |
| II-B | Sub-questions | **Refutable Sub-Questions and Their Falsification Conditions** |
| II-C | The two-estimand rule | **The Two-Estimand Rule: Observational and Mechanistic Attribution** |
| III | Related Work | **Related Work and Positioning** |
| III-a | *(paragraph)* Agreement and co-failure | **A. Cross-Sectional Agreement and Ensemble Co-Failure** |
| III-b | *(paragraph)* Variance decomposition of evaluation pipelines | **B. Variance Decomposition in Evaluation and Measurement Pipelines** |
| III-c | *(paragraph)* Lineage as structure | **C. Lineage Reconstruction and Phylogenetic Approaches** |
| III-d | *(paragraph)* Instrument-level bias and monoculture | **D. Instrument-Level Bias and the Algorithmic Monoculture Literature** |
| — | *(new)* | **E. Positioning: What Remains Unmeasured** |
| IV | Formal Model and Identifiability | **Formal Model, Estimands, and Identifiability Conditions** |
| IV-A | Setup and notation | **Population Model and Notation** |
| IV-B | Estimators | **Restricted-Maximum-Likelihood Estimation of the Variance Components** |
| IV-C | Estimands | **Observational and Mechanistic Estimands** |
| IV-D | Identifiability conditions | **Sufficient Conditions for Identifiability of the Partition** |
| — | *(new)* | **E. Computational Complexity of the Estimator** |
| V | Methodology | **Methodology: A Three-Gate Protocol for Identifiability-Preserving Measurement** |
| V-A | Study Population Construction | **Construction and Structural Validation of the Study Population** |
| V-B | Simulation Validation of the Estimator | **Simulation-Based Validation of the Proposed Estimator** |
| V-C | Pre-Analysis Study-Population Design | **Outcome-Independent Study-Population Optimization** |
| V-D | Trait Measurement and Decomposition | **Trait Measurement and Variance Decomposition Protocol** |
| VI | Results | **Results** *(keep)* |
| VI-A | Population Audit | **Structural Audit of the 47-Model Connected Subset** |
| VI-B | Simulation Validation | **Estimator Recovery and Detectable Failure Under the D1–D3 Battery** |
| VI-C | Pre-Analysis Population Design | **Selection of the Minimum Valid Population Under the G3 Gate** |
| VI-D | Empirical outputs (pending measurement) | **see §11-C — this heading cannot survive in its current form** |
| VII | Discussion and Intervention Implications | **Discussion: Operational Implications for Model Portfolio Design** |
| VIII | Threats to Validity and Limitations | **Threats to Validity, Scope Restrictions, and Limitations** |
| IX | Conclusion | **Conclusion and Future Work** |

## 5.3 Appendix restructuring

Consolidate seven micro-appendices into four substantive ones:

| New | Merges | Retitled |
|---|---|---|
| A | A (Phase 0 verification) | **Metadata Verification and Lineage Provenance** |
| B | B + D (identification argument + crossing/rank) | **Formal Identification Argument and the Crossing Condition** |
| C | C (D3 battery) | **Specification of the Detectable-Failure Battery** |
| D | E + F (REML/Woodbury + cost plan) | **Computational Implementation, Complexity, and Cost** |
| E | G (roster) | **Minimum Valid Population Roster** |

---

# PART 6 — VISUAL DENSITY AND THE PATH TO 18–20 PAGES

## 6.1 The arithmetic

Current: 5,564 body words + 1,122 appendix words = 6,686 words, occupying ~9.5 pages of real content stretched across 13.

After the §2 figure reflow reclaims ~2.6 pages, you have **~10.4 pages of content in a 10.4-page-equivalent document**. To reach 19 pages with 16 figures and 13 tables (which together consume ~6.5 pages), you need approximately **12,500 words of body text — an increase of about 5,800 words.**

That is a lot, and it must be real. Here is where it comes from. Every item below is content the paper is *currently missing*, not padding.

## 6.2 Where the 5,800 words come from

**§III Related Work: 836 → 2,200 words (+1,364).**
This is the largest and easiest gain. Thirteen references cannot support a journal Related Work section. Expand to 35–40 references across five subsections:
- Variance components and generalizability theory: you cite Harville, Patterson–Thompson, Brennan — add Searle/Casella/McCulloch, Bates et al. (lme4), and the REML small-sample literature (Kenward–Roger, Satterthwaite). Reviewer #1 will expect these by name.
- Benchmark evaluation and measurement error: expand beyond Messing and Hendrycks.
- Model lineage and provenance: PhyloLM and Li et al. are two points; the model-genealogy and model-fingerprinting literature is larger.
- Algorithmic monoculture: Hedden–Raghavan and Jo et al. are the right anchors; add the original monoculture framing and the downstream welfare work.
- Ensembling and diversity: Chen 2026 is one reference for what is a large literature on ensemble diversity–accuracy trade-offs.

**§VII Discussion: 247 → 1,100 words (+853).**
At 247 words this is not a Discussion; it is a paragraph. It must contain: (a) what each regime implies for portfolio construction, with numbers; (b) the co-failure ceiling connection developed properly rather than gestured at; (c) what a practitioner does *differently* on Monday morning under each outcome; (d) why the pairwise correlation that prior work reports is the wrong decision quantity; (e) honest limits of the recommendation. Supported by NF-10 and NF-12.

**§I Introduction: 516 → 1,100 words (+584).**
Add: a concrete motivating scenario (a real deployment where correlated failure bites); an explicit contributions list (IEEE Access convention — four to six numbered contributions); and a paper-organisation paragraph. The contributions list is genuinely important: an AE looks for it, and your contributions are currently spread across the abstract in prose.

**§IV Formal Model: 908 → 1,700 words (+792).**
Add: **Definition 1** (connected crossed design), **Proposition 1** (crossing ⇒ full column rank, currently a 110-word appendix), **Remark 1** (why the nested case is not a degenerate special case but a different estimand), and a new §IV-E on computational complexity feeding T-N3. Formal environments are the single most effective way to raise the perceived rigour of a statistics paper, and you already have the content — it is just written as prose in appendices.

**§V Methodology: 869 → 1,600 words (+731).**
Add **Algorithm 1** (G3 outcome-independent population optimiser) and **Algorithm 2** (REML fit with Woodbury and PSD clipping) as proper `algorithm` environments with numbered lines. A methods paper in IEEE Access with **zero algorithm boxes** is unusual and is noticed. Add design-rationale prose: why 5-shot, why MMLU, why per-question binary, why the era window is a quarter.

**§VIII Threats: 444 → 900 words (+456).**
The content here is good — this is the most intellectually honest section in the paper. It is compressed to the point of terseness. Give each of the nine threats a short paragraph: statement, magnitude bound, mitigation or carried-scope-restriction. Supported by NF-9.

**§IX Conclusion: 159 → 450 words (+291).**
Restate contributions concretely, state what the measurement pass will resolve, and give a real future-work paragraph (extension to closed models via API-only traits; extension beyond MMLU; longitudinal re-estimation as the population grows).

**Appendices: 1,122 → 1,900 words (+778).**
Consolidated per §5.3, with the identification argument written out properly rather than compressed to 151 words.

**Total: +5,849 words.** This lands at approximately **12,500 body words**, which with 16 figures and 13 tables produces **19–20 pages**.

## 6.3 What NOT to add

Do not add: a "Background on LLMs" section; a general tutorial on mixed models; restated equations; expanded abstract; or a longer conclusion that repeats the discussion. Every one of these is visible padding and Reviewer #2 will name it.

---

# PART 7 — TYPOGRAPHY REVIEW

**Critical:**
1. **Thirteen objects overflow their boxes** (see §0.1). Five clip at the trim edge and are physically cut off in print.
2. **Text/table overprint on page 7** — two text runs in the same physical space.
3. **Internal label overprint in Figs. 1 and 6** — `n0=21`/`winner`, `FAIL`/`PASS`, legend over `baseline`, annotation over "Error trait" node.
4. **Equation (5) overflows by 43.22 pt.** Break with `\begin{split}`.

**Major:**
5. **Figure fonts do not match the document.** All matplotlib figures use the default sans-serif (DejaVu Sans); the body is Times. IEEE Access figures should use a serif face at 8–9 pt. Set `rcParams['font.family']='serif'`, `rcParams['font.serif']=['Times New Roman','Nimbus Roman']`, `rcParams['font.size']=8`.
6. **Figure text is too small at print size.** Fig. 4's marker labels are ~5 pt after scaling. IEEE minimum for legible print is 8 pt *at final size*. Because the figures are being scaled down from 7.6 in to 6.99 in, all internal text shrinks by 8% — export at the target width so text size is what you specify.
7. **Figures carry internal titles.** Figs. 3, 4, 5, 6 all have matplotlib `suptitle`/`title` text. IEEE style puts this in the caption. Remove every internal title; it is duplicated content and it is what is getting clipped.
8. **Table 6's footnote marker** uses `*`; IEEE house style is superscript lowercase letters.
9. **Colour-only encoding.** Fig. 3's heatmap and Fig. 4's filled/open markers encode meaning by colour alone in places. IEEE Access is read in greyscale print. Add hatching or shape redundancy.
10. **Grey annotations in Fig. 4** (`Gemini-3 (closed)`, `GPT-4o (closed)`) are lighter than surrounding text and will drop out in print.

**Minor:**
11. **Orphaned section opening on page 4** — §V begins with two lines at the column foot.
12. **Column imbalance on pages 3 and 13** — one column entirely float, the other entirely text.
13. **Caption style is inconsistent.** Some captions open with a bold sentence fragment, some with a bold full sentence, some run to five lines. IEEE Access convention: a bold lead phrase, then explanatory sentences. Normalise all 8.
14. **Caption lengths range from 1 to 7 lines.** The Fig. 4 caption is 7 lines and contains material that belongs in the body text.
15. **`\PARstart` used once**, correctly, on page 1. Fine.
16. **Ten underfull `\hbox` warnings** — loose inter-word spacing, mostly in narrow table cells. Will resolve when the tables are widened.

**Cosmetic:**
17. Index terms are alphabetical but contain the near-duplicate pair "Correlated errors, error correlation."
18. `\markboth` running head is 91 characters and wraps close to the rule.
19. Inconsistent en-dash/em-dash usage in "family--error" vs "parent--offspring" contexts.
20. Table column heads are not consistently bold across the nine tables.

---

# PART 8 — IEEE ACCESS STYLE COMPLIANCE

## 8.1 Which journal does this look like?

**It does not currently look like any of them.** It looks like a well-typeset LaTeX preprint with production errors.

Setting the production errors aside and judging structure alone, the manuscript's DNA is **IEEE Transactions**, not IEEE Access: heavy formal apparatus, small figure count, prose-dominant appendices, terse discussion, minimal reference list. It is not Nature-like — Nature-style papers are figure-led with a single large multi-panel display per claim, and yours is text-led.

**The gap to IEEE Access house style, specifically:**

| Dimension | Typical IEEE Access AI paper | This manuscript | Gap |
|---|---|---|---|
| Length | 12–20 pages | 13 (≈9.5 real) | Content-thin |
| Body words | 8,000–15,000 | 5,564 | **−3,000 to −9,500** |
| Figures | 8–15 | 6 real + 2 placeholders | **−4** |
| Single-col : double-col figures | ≈3:1 | **0:8** | **Inverted** |
| Tables | 5–10 | 9 | OK |
| References | 30–60 | **13** | **−20 to −47** |
| Algorithm boxes | 1–3 in a methods paper | **0** | **−2** |
| Numbered contributions list | Near-universal | Absent | Missing |
| Graphical abstract | Requested (660×295, <45 KB) | Absent | Missing |
| Author photos | Standard | `nophoto`, `...` bios | Missing |

The **0:8 single-to-double column figure ratio is the most visually distinctive deviation.** Open any IEEE Access AI paper and you see a page rhythm of text-with-a-column-figure-at-the-top, occasionally interrupted by a full-width architecture diagram. Your paper has *only* the interruption. That is what makes it read as a conference paper stretched to fit — you correctly diagnosed this, and §2.1 gives you the one-line cause.

## 8.2 Making it visually indistinguishable from accepted IEEE Access papers

Nine concrete rules, in order of visual impact:

1. **Invert the figure width ratio to roughly 3:1 single:double.** Target 12 single-column and 4 double-column figures. This single change does more for "looks like IEEE Access" than everything else combined.
2. **Every page gets either a figure or a table, and no page gets more than one full-width float.** Currently pages 5, 6, 9, 11 have exactly one full-width float and nothing else of substance; pages 2 and 3 have two clipped tables each.
3. **Never let a float exceed 45% of a page.** Currently Fig. 4 is at 55% and Figs. 1, 2 at ~50%.
4. **Column figures live at the top of a column, never mid-column.** IEEE Access almost never wraps text around figures; the house rhythm is float-at-top.
5. **Caption formula:** bold lead phrase (5–10 words) → what is shown → what to conclude → cross-reference. Two to four lines. Normalise all captions to this.
6. **Serif figure fonts at 8 pt final size,** matching the body. This is the most common tell of a paper assembled from matplotlib defaults, and yours has it on every figure.
7. **No internal figure titles.** Caption only.
8. **Thirty-five or more references,** formatted in IEEEtran style. Reduce the proportion of arXiv-only citations — you currently have 8 of 13 as bare arXiv links, which reads as a preprint-era bibliography.
9. **Add the standard IEEE Access furniture:** numbered contributions list at the end of §I, a paper-organisation paragraph, a graphical abstract, real biographies with photographs.

## 8.3 A note on the comparison you asked for

You asked me to compare against ten specific recent IEEE Access AI papers. I want to be straight with you about what I actually did: I verified the **official IEEE Access and IEEE Author Center requirements** (graphics widths, resolution, submission rules, length and reference norms) from primary sources, and the **page geometry from your own `ieeeaccess.cls`**. The house-style characterisation in §8.1–8.2 reflects the IEEE Access corpus as I know it, but I did not open ten named 2024–2026 papers and tabulate their figure counts, so treat that row of the table as a well-founded norm rather than a measured statistic.

If you want that comparison measured rather than asserted, it is a genuinely useful exercise and cheap to do yourself: pull ten recent IEEE Access AI papers from your own subject area, and for each record page count, figure count, single-vs-double-column split, table count, and reference count. Twenty minutes of work, and it will either confirm the targets above or sharpen them. I would recommend doing it before the final figure regeneration pass, so you only redraw once.

---

# PART 9 — PROFESSIONALISM SCORES

Scored against the top 5% of IEEE Access submissions. These are deliberately harsh.

| Dimension | Score | Justification |
|---|---|---|
| **Title** | **8/10** | Genuinely strong. Poses a question, names the method, names the object. |
| **Abstract** | **6/10** | Well written but 30% overlong, unbroken, and ends by conceding no result. |
| **Introduction** | **4/10** | 516 words. No contributions list, no organisation paragraph, no motivating scenario. |
| **Related Work** | **3/10** | 836 words, 13 references, level-4 headings used as level-2, differentiation table illegible. |
| **Methodology** | **6/10** | The three-gate protocol is a real contribution, but zero algorithm boxes and thin rationale. |
| **Mathematics** | **6/10** | Correct and careful. No formal environments; identifiability proof compressed to 110 words in an appendix; equation (5) overflows. |
| **Figures** | **1/10** | Two are placeholders. All eight overflow. Two clip at trim. Three have internal overprint. One displays four identical numbers. Zero single-column. |
| **Tables** | **4/10** | Good content, well chosen. Five overflow; two clip at trim; one overprints body text; two should be merged. |
| **Results** | **3/10** | Phases 0 and 1 are solid. Section VI-D is six bullets, five ending in *(TBD)*. |
| **Discussion** | **2/10** | 247 words. This is the section that carries the paper's meaning. |
| **Threats** | **7/10** | Best section in the paper. Genuinely self-critical, well reasoned, badly compressed. |
| **Appendices** | **4/10** | Seven fragments averaging 160 words. Real content, poor packaging. |
| **Typography** | **2/10** | Thirteen overflows, one overprint collision, mixed heading case, sans-serif figures. |
| **Layout** | **2/10** | Six of thirteen pages below 60% density. Figure ratio inverted 0:8. |
| **Overall visual quality** | **2/10** | A reader's first impression is "unfinished." |
| **Publication readiness** | **1/10** | Placeholder figures in the submitted PDF. Would not pass validation. |

**Weighted overall: 3.6/10.**

The distribution matters more than the mean: the *scholarship* scores (title, methodology, mathematics, threats) average 6.75, while the *presentation* scores (figures, typography, layout, readiness) average 1.75. **There is a good paper inside this document that is being actively hidden by its own production.** That is an encouraging finding, because presentation is the cheap axis to fix.

---

# PART 10 — MISSING CONTENT

Beyond the 12 figures (§3) and 6 tables (§4):

1. **Algorithm 1 — G3 outcome-independent population optimiser.** Numbered lines, explicit inputs, explicit assertion that trait values are never read. This algorithm *is* the paper's second contribution and it currently exists only as prose.
2. **Algorithm 2 — REML fit via Woodbury with PSD clipping.** Log-variance reparameterisation, Woodbury solve, Hessian, Monte-Carlo share CIs.
3. **Definition 1 — connected crossed design.** Used throughout; never formally defined.
4. **Proposition 1 + proof — crossing implies full column rank.** Currently Appendix D, 110 words. Promote to the main text as a numbered proposition with the proof in the appendix.
5. **Remark 1 — the nested case is a different estimand, not a degenerate one.** Prevents the most likely reviewer misreading.
6. **Numbered contributions list** at the end of §I. Four to six items.
7. **Paper organisation paragraph** at the end of §I.
8. **Running example** — one family, one quarter, one MMLU item, carried through §IV as a concrete anchor (feeds NF-4).
9. **Complexity analysis subsection** (§IV-E) feeding T-N3.
10. **Reproducibility statement** with artifact locations, feeding T-N4.
11. **Graphical abstract** — 660×295 JPG under 45 KB. Required at submission; currently absent.
12. **Real author biographies and photographs.** Both bios currently contain the literal string `His research interests include ... .`
13. **Completed `\history`, `\doi`, `\tfootnote`, and Acknowledgment.** All are visible placeholder text in the rendered PDF.
14. **AI-use disclosure in the Acknowledgment** if applicable — IEEE Access requires disclosure of AI-generated content with the system identified.
15. **Twenty-two or more additional references** (§6.2).

---

# PART 11 — CAMERA-READY ACTION LIST

## 11-A. CRITICAL — nothing else matters until these are done

| # | Action | Effort |
|---|---|---|
| C1 | Add `[width=\textwidth]` to the 4 retained `\Figure` calls; regenerate the figures at exactly 6.99 in / 3.5 in. **Eliminates all 8 figure overflows.** | 1 h |
| C2 | Convert Tables 1, 2, 4, 6 to `table*` with `p{}` columns. **Eliminates the 4 worst overflows and the page-7 overprint.** | 2 h |
| C3 | **Resolve the placeholder-figure problem** (§11-C). No submitted PDF contains a "FIGURE PLACEHOLDER" box. | — |
| C4 | Fix the internal overprints in Figs. 1 and 6 (`n0=21`/`winner`, `FAIL`/`PASS`, legend/`baseline`, annotation over "Error trait"). | 2 h |
| C5 | Remove internal titles from all figures; move to captions. | 0.5 h |
| C6 | Fill `\history`, `\doi`, `\tfootnote`, Acknowledgment; write real biographies. | 1 h |
| C7 | Break equation (5) with `\begin{split}`. | 0.25 h |

**Critical subtotal: ~7 hours.** This is the highest-return work in this document. It converts the paper from "would not pass validation" to "would reach a reviewer," and it is almost entirely mechanical.

## 11-B. MAJOR — required to be competitive

| # | Action | Effort |
|---|---|---|
| M1 | Expand Related Work to ~2,200 words and 35–40 references | 8 h |
| M2 | Expand Discussion 247 → 1,100 words | 4 h |
| M3 | Write Algorithms 1 and 2 as `algorithm` environments | 3 h |
| M4 | Add Definition 1, Proposition 1, Remark 1; promote the identification argument | 3 h |
| M5 | Expand Introduction to ~1,100 words with numbered contributions | 3 h |
| M6 | Convert 4 retained figures to the 3:1 single:double ratio; merge Figs. 3+4 | 4 h |
| M7 | Delete Fig. 5; build T-N2 | 1 h |
| M8 | Build the 6 new tables (§4.2) | 4 h |
| M9 | Build 6 highest-value new figures: NF-1, NF-2, NF-5, NF-9, NF-10, NF-11 | 10 h |
| M10 | Expand Threats to ~900 words; Conclusion to ~450 | 3 h |
| M11 | Restructure appendices 7 → 5 (§5.3) | 2 h |

**Major subtotal: ~45 hours.**

## 11-C. The strategic decision you must make first

**Section VI-D contains six bullets, five ending in the literal string *(TBD)*, and two placeholder figures.** No amount of layout work fixes this. There are three honest options, and they lead to genuinely different papers:

**Option 1 — Run the eval pass (recommended if at all feasible).**
You have the full pipeline, the population file, the cost plan (710 GPU-min for 22 models, ~$40–80 on rented H200s), and the runbook. Executing it turns a protocol paper into a research paper with a result. **This roughly doubles the paper's acceptance probability on its own** and makes Figs. 7 and 8 real. Everything in this report gets easier if you do this.

**Option 2 — Reframe as a methodology paper and delete the empirical section.**
Cut §VI-D and Figs. 7–8 entirely. Retitle around the *instrument*: the three-gate protocol, the validated estimator, and the outcome-independent population optimiser are a legitimate contribution without the empirical partition. Rewrite the abstract to lead with the instrument. The paper becomes shorter before it becomes longer, but it becomes *honest and complete* — which is what an AE is actually checking for. Then expand per Part 6.

**Option 3 — Keep the pending framing.** I would advise against it. IEEE Access has no registered-report track, and an AE reading "*(TBD)*" five times in a Results section will not send it to review.

**Options 1 and 2 both produce a publishable paper. Option 3 does not.** This decision gates roughly 15 hours of the work below it, so make it before starting Part 6.

## 11-D. MINOR

| # | Action | Effort |
|---|---|---|
| N1 | Title Case all 15 subsection headings | 0.5 h |
| N2 | Apply the heading rewrites in §5.2 | 1 h |
| N3 | Convert Related Work `\paragraph` → `\subsection` | 0.5 h |
| N4 | Merge Tables 8 + 9 | 1 h |
| N5 | Split and trim the abstract to 240 words in two paragraphs | 1 h |
| N6 | Normalise all captions to the §8.2 formula | 2 h |
| N7 | Serif fonts at 8 pt across all figures | 1 h |
| N8 | Build the remaining 6 figures (NF-3, NF-4, NF-6, NF-7, NF-8, NF-12) | 8 h |
| N9 | Fix Table 6 footnote markers to IEEE style | 0.25 h |
| N10 | Create the graphical abstract (660×295, <45 KB) | 1 h |

**Minor subtotal: ~16 hours.**

## 11-E. COSMETIC

Index-term revision (0.25 h) · greyscale-safe encoding in Figs. 3–4 (1 h) · dash consistency (0.5 h) · bold table heads (0.5 h) · widow/orphan pass on the final build (1 h). **~3 hours.**

## 11-F. Projected outcome

| Metric | Now | After Critical | After Critical+Major | Full pass |
|---|---|---|---|---|
| Pages | 13 (≈9.5 real) | 12 (dense) | 17–18 | **19–20** |
| Figures | 6 real + 2 placeholder | 6 | 12 | **16** |
| — single : double column | 0 : 8 | 4 : 2 | 8 : 4 | **12 : 4** |
| Tables | 9 (5 clipped) | 9 (0 clipped) | 13 | **13** |
| References | 13 | 13 | 35+ | **40** |
| Body words | 5,564 | 5,564 | ~11,000 | **~12,500** |
| Overfull boxes | **13** | **0** | 0 | **0** |
| Algorithm boxes | 0 | 0 | 2 | **2** |
| Overall score | 3.6/10 | 5.5/10 | 7.5/10 | **8.5/10** |

**Total effort: ~71 hours** (7 critical + 45 major + 16 minor + 3 cosmetic), excluding the eval pass itself under Option 1.

**Acceptance probability.** I will give you ranges rather than false precision:
- **As submitted today:** near zero — stopped at validation or desk-rejected.
- **After Critical only (7 h):** reaches a reviewer, but a 13-page, 13-reference, no-result paper is a likely reject-or-major-revision.
- **After Critical + Major, under Option 2 (methodology framing):** a credible submission. The instrument is a real contribution and the threats section is genuinely strong.
- **After the full pass, under Option 1 (with the eval pass run):** a strong submission — a validated novel estimator, a pre-registered design, a real empirical partition, and a clear practitioner implication. This is the version worth aiming for.

---

## Closing note to the authors

The instinct behind your original brief was right — this manuscript does not yet look like IEEE Access, and it is wasting vertical space. But the diagnosis was incomplete in an important way: the wasted space is not a page-design preference, it is **eight figures that overflow the text block because a single optional LaTeX argument was never supplied**, and it is costing you 2.6 pages of white space plus five objects that are physically cut off at the trim.

The good news is that the scholarship scores nearly twice what the presentation does. The three-gate protocol, the outcome-independent population optimiser, and the D3 must-fail battery are real, defensible contributions, and the Threats section is more honest than most published work. What is failing here is production, not thinking — and production is the cheap axis.

Fix the seven Critical items first. They take a day, and they change the paper's category.
