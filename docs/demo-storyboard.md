# SharpeLab Demo Video Storyboard

> **Total Video Runtime:** 3:00 (180 Seconds)
> **Resolution:** 1920x1080 (1080p)
> **Audio:** Clear voiceover commentary aligned with visual interaction.

---

## Scene Breakdown

### Scene 1: Introduction & Product Framing
- **Time Window**: 0:00 - 0:20 (20s)
- **Screen**: SharpeLab Visual Explorer header bar, brand tagline (*"The data did not disagree. The assumptions did."*), and initial scenario tab `[ Sensitive to assumptions ]`.
- **Narration**: *"Every day, quantitative decisions rely on Sharpe ratios. But standard software calculates confidence intervals assuming independent returns. When autocorrelation is present, standard formulas fail silently. Welcome to SharpeLab."*
- **Click**: None (Mouse hovers over brand tagline and disclosure badges).
- **Expected Visual**: Crisp dark-mode header with cyan branding and "Deterministic Offline Replay" badge.

---

### Scene 2: The Two Analysts Mystery
- **Time Window**: 0:20 - 0:40 (20s)
- **Screen**: Section A — Analyst Cards comparison (Analyst A Naive IID vs Analyst B Dependence-Aware HAC).
- **Narration**: *"Two analysts receive the exact same 250 return observations. Both calculate the exact same Sharpe estimate of 0.1253. But Analyst A reports a significant positive result, while Analyst B reports zero overlap. Same data. Same estimate. Opposite conclusions. Why?"*
- **Click**: Mouse highlights 3-part contrast metrics (Estimate: 0.1253, SE: 0.0635 vs 0.0851, CI bounds).
- **Expected Visual**: Red border on Analyst Card A (`NOT ADMISSIBLE`), green border on Analyst Card B (`SUPPORTED BY EVIDENCE`).

---

### Scene 3: Revealing Scenario 1 (Sensitive to Assumptions)
- **Time Window**: 0:40 - 2:10 (90s)
- **Screen**: Sections B (Evidence Matrix), C (Admissibility Route), and D (Final Verdict Banner).
- **Narration**: *"Let's reveal the hidden assumption. The Ljung-Box test detects autocorrelation ($p = 3.00 \times 10^{-6}$), contradicting independence. SharpeLab rules Naive IID 'Not scientifically admissible' and selects Bartlett HAC. Uncertainty expands by +34%, causing the confidence interval to cross zero. Verdict: Sensitive to assumptions."*
- **Click**: **CLICK** `[ Reveal hidden assumption ]` button at 0:45.
- **Expected Visual**: Smooth CSS reveal of Evidence Matrix (`CONTRADICTS IID`), Admissibility Table (`Not scientifically admissible`), horizontal confidence interval chart with zero line crossing, and amber Verdict Banner **“Sensitive to assumptions”**.

---

### Scene 4: Scenario 2 (Robust Under Volatility)
- **Time Window**: 2:10 - 2:40 (30s)
- **Screen**: Scenario Switcher Tab 2 — `[ Robust under volatility ]`.
- **Narration**: *"Does SharpeLab always overturn an analysis? No! Switching to 'Robust under volatility', ARCH-LM detects volatility clustering. Naive IID is again inadmissible, but every admissible robust method—both HAC and Bootstrap—confirms $CI > 0$. Verdict: Robust."*
- **Click**:
  1. **CLICK** tab `[ Robust under volatility ]` at 2:10.
  2. **CLICK** `[ Reveal hidden assumption ]` button at 2:20.
- **Expected Visual**: Instant content reset, green Verdict Banner **“Robust”**, confidence interval chart showing both HAC & Bootstrap bars strictly to the right of zero (`[0.0391, 0.3033]` & `[0.0686, 0.2779]`).

---

### Scene 5: Scenario 3 (Cannot Conclude / Structural Shift)
- **Time Window**: 2:40 - 3:10 (30s)
- **Screen**: Scenario Switcher Tab 3 — `[ Cannot conclude ]`.
- **Narration**: *"What if data undergo a structural shift? Under a mean break, Split-Chow detects instability. Standard software computes a full-sample Sharpe ratio anyway. SharpeLab deterministically abstains, issuing the verdict: Cannot conclude."*
- **Click**:
  1. **CLICK** tab `[ Cannot conclude ]` at 2:40.
  2. **CLICK** `[ Reveal hidden assumption ]` button at 2:50.
- **Expected Visual**: Red Verdict Banner **“Cannot conclude”**, Structural Break Visual Strip highlighting sub-sample mean shift (-0.010 vs +0.030), and full-sample estimators marked `Abstained`.

---

### Scene 6: Architecture & Audit Log Closing
- **Time Window**: 3:10 - 3:40 (30s)
- **Screen**: Collapsible Audit Log Drawer and system summary.
- **Narration**: *"Every diagnostic request, eligibility rule, and verdict is recorded in an unalterable audit trail. SharpeLab does not ask whether a calculation is mathematically valid. It asks whether the conclusion survives every scientifically admissible interpretation of the data. Thank you!"*
- **Click**: **CLICK** `[ ▸ View Audit Trail Log (#evt-8f92a10c) ]` at 3:15.
- **Expected Visual**: Expanded monospace audit event log (`[orchestrator] workflow-started`, `[deterministic-core] final-decision`).

---

## Storyboard Runtime Summary

| Scene | Subject | Duration | Cumulative Time |
| :--- | :--- | :---: | :---: |
| Scene 1 | Introduction & Product Framing | 20s | 0:20 |
| Scene 2 | The Two Analysts Mystery | 20s | 0:40 |
| Scene 3 | Scenario 1: Sensitive to Assumptions | 90s | 2:10 |
| Scene 4 | Scenario 2: Robust Under Volatility | 30s | 2:40 |
| Scene 5 | Scenario 3: Cannot Conclude | 30s | 3:10 |
| Scene 6 | Architecture & Audit Log Closing | 30s | 3:40 |

**Total Video Duration:** Exactly 3:40 (or 3:00 tight edit).
