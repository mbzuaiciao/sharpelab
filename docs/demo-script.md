# SharpeLab Three-Minute Live Presentation Script

> **Total Runtime:** Exactly 3 Minutes (180 Seconds)
> **Presenter Goal:** Demonstrate how SharpeLab surfaces hidden statistical assumption failures, governs method eligibility, and evaluates conclusion robustness across admissible specifications.

---

## Script Overview & Timeline

| Segment | Target Time | Action / Clicks | Focus |
| :--- | :---: | :--- | :--- |
| **1. Opening** | 0:00 - 0:20 (20s) | Initial Screen (`ar1-assumption-sensitive`) | Introduce tagline and core thesis |
| **2. The Problem** | 0:20 - 0:40 (20s) | Highlight Analyst Cards A & B | The "Two Analysts, Same Data" Hook |
| **3. Scenario 1 (Sensitive)** | 0:40 - 2:10 (90s) | **CLICK:** `[ Reveal hidden assumption ]` | Diagnostic Evidence, Admissibility, Verdict |
| **4. Scenario 2 (Robust)** | 2:10 - 2:40 (30s) | **CLICK:** `[ Robust under volatility ]` | Confirming conclusions across valid specs |
| **5. Scenario 3 (Abstain)** | 2:40 - 3:10 (30s) | **CLICK:** `[ Cannot conclude ]` | Structural break & automatic abstention |
| **6. Architecture & Closing**| 3:10 - 3:40 (30s) | Scroll / Audit Trail Drawer | Governance core & auditable verdict |

---

## Full Presentation Script

### 1. Opening (0:00 - 0:20) — 20 Seconds
**[Visual: Initial browser screen showing SharpeLab header and Scenario 1]**

> *"Hello! Every day, portfolio managers and quantitative risk committees make allocation decisions based on Sharpe ratio estimates. But standard statistical software almost always returns a confidence interval when asked—even when the underlying mathematical model is completely invalid for the data.*
>
> *Welcome to **SharpeLab**. Our tagline is: **The data did not disagree. The assumptions did.***"

---

### 2. The Problem (0:20 - 0:40) — 20 Seconds
**[Visual: Mouse hovers over Analyst Card A (Naive IID) and Analyst Card B (HAC)]**

> *"Look at this opening scenario. Two analysts receive the exact same return series of 250 observations. Both calculate the exact same Sharpe ratio estimate of **0.1253**.*
>
> *Yet Analyst A concludes the Sharpe ratio is significantly positive ($CI = [0.0008, 0.2497]$), while Analyst B concludes the result cannot be distinguished from zero ($CI = [-0.0415, 0.2921]$).*
>
> *Same data. Same Sharpe estimate. Opposite conclusions. Why?"*

`[PAUSE 2 SECONDS FOR EFFECT]`

---

### 3. Scenario 1: Sensitive to Assumptions (0:40 - 2:10) — 90 Seconds

**[Action: PRESS BUTTON `[ Reveal hidden assumption ]` at 0:45]**

> *"Let's reveal the hidden assumption.*
>
> *When we click **Reveal hidden assumption**, SharpeLab runs deterministic diagnostics on the return series.
> Look at the Evidence Matrix: The **Ljung-Box test** detects significant linear autocorrelation ($p = 3.00 \times 10^{-6}$). Today's return contains information about later returns.*
>
> *This empirically **contradicts** the independence assumption required for standard Gaussian formulas.*

`[PAUSE 2 SECONDS — Point mouse to Section 2: Scientific Admissibility Route]`

> *Because the independence assumption is violated, SharpeLab's deterministic eligibility router marks the Naive IID Gaussian method as **Not scientifically admissible**.*
>
> *Instead, it selects **Bartlett Newey-West HAC** as the primary admissible estimator and **Circular Block Bootstrap** as a sensitivity cross-check.*
>
> *Notice what happened to uncertainty: Accounting for autocorrelation expands the standard error by **34%**, causing the 95% confidence interval to cross zero.*
>
> *SharpeLab issues a formal verdict: **Sensitive to assumptions**.*
>
> *The positive conclusion relied on an independence assumption that the data contradicted."*

---

### 4. Scenario 2: Robust (2:10 - 2:40) — 30 Seconds

**[Action: CLICK SCENARIO SWITCHER `[ Robust under volatility ]` at 2:10]**

> *"Now, does SharpeLab always overturn an analysis? No!
>
> Let's switch to our second scenario: **Robust under volatility**.*

**[Action: PRESS BUTTON `[ Reveal hidden assumption ]` at 2:20]**

> *Here, the diagnostic matrix detects volatility clustering—ARCH-LM $p = 4.67 \times 10^{-5}$. Once again, naive IID is ruled inadmissible.*
>
> *However, when we evaluate every scientifically admissible robust method—both Bartlett HAC ($CI = [0.0391, 0.3033]$) and Circular Block Bootstrap ($CI = [0.0686, 0.2779]$)—both confidence intervals remain strictly above zero.*
>
> *SharpeLab issues the verdict: **Robust**. The uncertainty model changed, but every valid method agrees."*

---

### 5. Scenario 3: Cannot Conclude (2:40 - 3:10) — 30 Seconds

**[Action: CLICK SCENARIO SWITCHER `[ Cannot conclude ]` at 2:40]**

> *"Finally, what happens when data undergo a major structural shift?
>
> Let's select **Cannot conclude**.*

**[Action: PRESS BUTTON `[ Reveal hidden assumption ]` at 2:50]**

> *Here, the Split-Chow test detects a material mean break midway through the evaluation window.
>
> Standard software will happily calculate a single full-sample Sharpe ratio anyway. But SharpeLab recognizes that population parameters do not exist under structural instability.*
>
> *The deterministic workflow **abstains**, ruling all full-sample estimators inadmissible and issuing the verdict: **Cannot conclude**."*

---

### 6. Architecture & Closing (3:10 - 3:40) — 30 Seconds

**[Action: CLICK `[ ▸ View Audit Trail Log ]` at 3:15]**

> *"Behind the scenes, SharpeLab combines deterministic statistical routing with structured Phase 4A audit agents. Every diagnostic request, eligibility decision, and proposal rejection is recorded in an unalterable audit log.*
>
> *SharpeLab does not ask whether a calculation is mathematically valid. It asks whether the conclusion survives every scientifically admissible interpretation of the data.*
>
> *Thank you!"*

---
*End of Script. Total Runtime: 3:00.*
