# SharpeLab Hackathon Demonstration Plan

> **Tagline:** *The data did not disagree. The assumptions did.*
>
> **Core Value Proposition:** *SharpeLab does not ask whether a calculation is mathematically valid. It asks whether the conclusion survives every scientifically admissible interpretation of the data.*

---

## 1. Executive Summary

SharpeLab is an auditable, evidence-governed assumption and robustness explorer for quantitative risk and performance analysis. Quantitative decision-making frequently fails not because of mathematical error, but because analyst assumptions (such as independent and identically distributed returns or stationarity) are hidden inside standard formulas.

SharpeLab makes these hidden assumptions visible. Opening with a narrative hook of two analysts receiving the exact same return series but reaching opposing conclusions, SharpeLab exposes the statistical evidence behind the data, evaluates candidate inference methods under deterministic admissibility rules, tests conclusion invariance across all admissible specifications, and issues a formal top-level verdict: **ROBUST**, **ASSUMPTION-SENSITIVE**, or **ABSTAIN**.

This document establishes the architecture, visual wireframe, scenario validation, formal verdict definitions, and execution plan for the SharpeLab hackathon demo.

---

## 2. Product Thesis

Statistical software almost always returns a confidence interval or p-value when requested, even when the underlying data severely violate the procedure's statistical assumptions. In financial risk analysis, standard software calculates naive Gaussian Sharpe ratio confidence intervals even on data with strong autocorrelation, volatility clustering, or structural shifts.

SharpeLab shifts the paradigm from *“computing a number under unverified assumptions”* to *“auditing whether a conclusion is robust across all scientifically admissible assumptions.”* 

- **Data is invariant**: The raw return series $y_t$ is identical for all stakeholders.
- **Assumptions vary**: Analysts select different inference specifications (e.g. Naive IID vs Bartlett HAC vs Circular Block Bootstrap).
- **Assumptions must be governed**: SharpeLab evaluates typed statistical evidence against deterministic eligibility rules, ruling out invalid methods and determining whether the final decision changes across admissible specifications.

---

## 3. User Problem

Portfolio managers, risk committees, and financial regulators face a recurring challenge:
1. Two internal analysts or fund managers present conflicting Sharpe ratio estimates or risk conclusions for the same asset or strategy.
2. Analyst A uses standard software tools assuming IID Gaussian returns and reports a statistically significant Sharpe ratio ($p < 0.05$).
3. Analyst B applies robust Newey-West/HAC or block bootstrap adjustments and reports that the Sharpe ratio is not statistically distinguishable from zero ($p > 0.05$).
4. Decision-makers cannot easily verify which analyst is correct because the underlying assumptions are implicit.

SharpeLab solves this by automatically surfacing the typed statistical evidence (autocorrelation, ARCH effect, structural stability), classifying candidate methods as admissible or inadmissible, and proving whether the decision is assumption-sensitive or robust.

---

## 4. Judge Takeaway

After a 3-minute demo, hackathon judges will understand:
1. **The Core Problem**: Standard financial metrics silently mask critical statistical assumption failures.
2. **The Mechanism**: Evidence-Routed Statistical Inference (ERI) acquires typed statistical evidence (Ljung-Box, ARCH-LM, Chow break) and uses deterministic guardrails to govern method eligibility.
3. **The AI/Agent Role**: Specialized Phase 4A agents audit prose provenance, plan diagnostic requests, and generate traceably cited reports, while an authoritative deterministic adjudicator strictly enforces admissibility and computes math.
4. **The Product Value**: Decision-makers receive one auditable, non-hallucinated verdict (**ROBUST**, **ASSUMPTION-SENSITIVE**, or **ABSTAIN**) with an unalterable audit log.

---

## 5. Three-Minute Storyboard

```
[0:00 - 0:30] THE HOOK: TWO ANALYSTS DISAGREE
┌────────────────────────────────────────────────────────────────────────┐
│ • Select Scenario: "Serial Autocorrelation (AR1, Seed 4003)"          │
│ • Analyst A (Naive IID) reports: SR = 0.125, CI = [0.001, 0.250] (PASS)│
│ • Analyst B (Robust HAC) reports: SR = 0.125, CI = [-0.042, 0.292](FAIL│
│ • Question: Who is right? The data is identical!                       │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
[0:30 - 1:15] STEP 1: TYPED STATISTICAL EVIDENCE
┌────────────────────────────────────────────────────────────────────────┐
│ • SharpeLab runs deterministic diagnostics on the return series        │
│ • SURFACES: Ljung-Box linear dependence test p = 3.0e-06 (CONTRADICTS) │
│ • SURFACES: ARCH-LM squared dependence test p = 0.333 (INCONCLUSIVE)   │
│ • CONCLUSION: Linear serial dependence is empirically present.        │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
[1:15 - 2:00] STEP 2: DETERMINISTIC ELIGIBILITY ROUTING
┌────────────────────────────────────────────────────────────────────────┐
│ • Naive IID Gaussian: INELIGIBLE (Violates temporal IID assumption)    │
│ • Mertens / PSR: INELIGIBLE (Violates IID assumption basis)            │
│ • HAC Bartlett: ADMISSIBLE (Weak-dependence robust)                   │
│ • Block Bootstrap: ADMISSIBLE (Weak-dependence robust)                │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
[2:00 - 2:30] STEP 3: MULTI-SPECIFICATION ROBUSTNESS TEST
┌────────────────────────────────────────────────────────────────────────┐
│ • Decision Rule: Benchmark Hurdle SR > 0.0 at 95% Confidence          │
│ • Under Naive IID (Ineligible): Passes hurdle (CI_lower = 0.0008 > 0)  │
│ • Under Admissible Specs (HAC & Bootstrap): Fails hurdle (CI_lower<=0) │
└────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
[2:30 - 3:00] STEP 4: VERDICT & ABSTENTION DEMO
┌────────────────────────────────────────────────────────────────────────┐
│ • Final Verdict: ASSUMPTION-SENSITIVE (Decision flips under valid spec)│
│ • Switch Scenario to "Structural Break (Seed 4303)"                    │
│ • Chow break test fails -> Final Verdict: ABSTAIN (Inference invalid)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Single-Screen Information Architecture

The SharpeLab UI uses a single-screen investigative interface divided into four primary vertical visual regions:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ HEADER: SharpeLab Explorer | Scenario Switcher | Decision Hurdle Setting │
├──────────────────────────────────────────────────────────────────────────┤
│ SECTION 1: DISAGREEMENT HOOK                                             │
│ ┌──────────────────────────────┐    ┌──────────────────────────────────┐ │
│ │ Analyst A: Naive IID         │ vs │ Analyst B: Robust HAC            │ │
│ │ SR = 0.1253 | CI=[0.001,0.250]│    │ SR = 0.1253 | CI=[-0.042, 0.292]  │ │
│ │ Status: PASSES HURDLE        │    │ Status: FAILS HURDLE             │ │
│ └──────────────────────────────┘    └──────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│ SECTION 2: DIAGNOSTIC EVIDENCE MATRIX                                    │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ Test: Ljung-Box (Linear Dep.)   | p = 3.0e-06 | [ CONTRADICTS IID ]  │ │
│ │ Test: ARCH-LM (Volatility Clust)| p = 0.3330  | [ INCONCLUSIVE ]     │ │
│ │ Test: Chow Test (Stability)     | p = 0.4200  | [ SUPPORTS STABLE ]  │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│ SECTION 3: ADMISSIBLE INTERPRETATIONS & SENSITIVITY FOREST PLOT         │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ [INELIGIBLE] Naive IID Gaussian: Temporal dependence violates IID    │ │
│ │ [INELIGIBLE] Mertens / PSR:      Temporal dependence violates IID    │ │
│ │ [ADMISSIBLE] HAC Bartlett:       Primary robust specification        │ │
│ │ [ADMISSIBLE] Block Bootstrap:    Sensitivity specification           │ │
│ │                                                                      │ │
│ │ Forest Plot: Naive IID (Gray/X) | HAC (Blue) | Bootstrap (Blue)     │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│ SECTION 4: SHARPELAB VERDICT BANNER                                      │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ VERDICT: ASSUMPTION-SENSITIVE                                        │ │
│ │ Reason: Conclusion fails hurdle across admissible specifications.    │ │
│ │ Audit Log Trace ID: #evt-8f92a10c (Audit Trail Drawer ▾)             │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Text Wireframe

```text
================================================================================
SHARPELAB // Evidence-Governed Robustness Explorer
================================================================================
Scenario: [ AR(1) Serial Dependence (Seed 4003) ▾ ]  Hurdle: [ SR > 0.0 (95% CI) ]

--------------------------------------------------------------------------------
[1] THE NARRATIVE HOOK: TWO ANALYSTS, ONE RETURN SERIES
--------------------------------------------------------------------------------
Analyst A (Standard Gaussian Formula)      Analyst B (Heteroskedastic / HAC)
Sharpe Ratio : 0.1253                      Sharpe Ratio : 0.1253
Standard Err : 0.0635                      Standard Err : 0.0851 (+34% SE)
95% Conf Int : [0.0008, 0.2497]            95% Conf Int : [-0.0415, 0.2921]
Decision     : PASS (CI_lower > 0)         Decision     : FAIL (CI_lower <= 0)

--------------------------------------------------------------------------------
[2] TYPED STATISTICAL EVIDENCE MATRIX
--------------------------------------------------------------------------------
Diagnostic Property      Test Name        Statistic  p-value    Evidence Direction
-----------------------  ---------------  ---------  ---------  ------------------
Linear Dependence        Ljung-Box Q      28.5140    3.00e-06   CONTRADICTS IID
Squared Dependence       ARCH-LM          1.0541     3.33e-01   INCONCLUSIVE
Distribution Shape       Jarque-Bera      2.5480     2.80e-01   INCONCLUSIVE
Structural Stability     Split-Chow       0.8912     4.20e-01   SUPPORTS STABILITY

--------------------------------------------------------------------------------
[3] DETERMINISTIC METHOD ELIGIBILITY & ADMISSIBILITY ROUTE
--------------------------------------------------------------------------------
[ ✕ INELIGIBLE ] iid-gaussian-sharpe   : Rejection: Temporal dependence present.
[ ✕ INELIGIBLE ] mertens-psr           : Rejection: IID basis violated.
[ ✓ ADMISSIBLE ] hac-sharpe            : Primary: Weak-dependence robust (BW=2).
[ ✓ ADMISSIBLE ] block-bootstrap       : Sensitivity: Circular block (L=10, B=1000).

Sensitivity Forest Plot:
  iid-gaussian-sharpe   :  ├───|───┤  (CI > 0)   [INELIGIBLE - VOID]
  hac-sharpe            : ├────|────┤ (CI <= 0)  [PRIMARY ADMISSIBLE]
  block-bootstrap       : ├────|────┤ (CI <= 0)  [SENSITIVITY ADMISSIBLE]

--------------------------------------------------------------------------------
[4] SHARPELAB FINAL VERDICT
--------------------------------------------------------------------------------
┌──────────────────────────────────────────────────────────────────────────────┐
│  VERDICT: ASSUMPTION-SENSITIVE                                               │
│  The data did not disagree. The assumptions did.                              │
│  The conclusion is positive under ineligible Naive IID assumptions, but      │
│  fails to exceed zero under all admissible robust specifications.             │
│  Audit Event Hash: #894a8ca250bd  [ View Full Audit Log ]                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Existing-Component Reuse Map

| Architectural Component | File Path | Reuse Strategy | Adapter / Modification Needed |
| :--- | :--- | :--- | :--- |
| **Statistical Diagnostics** | [registry.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/diagnostics/registry.py) | **100% Direct Reuse** | None. Returns typed `DiagnosticResult` objects. |
| **Inference Estimators** | [gaussian.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/inference/gaussian.py), [hac.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/inference/hac.py), [block_bootstrap.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/inference/block_bootstrap.py) | **100% Direct Reuse** | None. Runs point estimates, standard errors, and CIs. |
| **Eligibility Router** | [eligibility.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/routing/eligibility.py), [router.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/routing/router.py) | **100% Direct Reuse** | None. Classifies candidate methods into `eligible` and `sensitivity_only`. |
| **Phase 4A Workflow** | [workflow.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/orchestration/workflow.py) | **100% Direct Reuse** (in `mode="mock"`) | None. Orchestrates evidence collection, mock agent calls, and adjudicator vetoes. |
| **Synthetic Generators** | [ar1.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/simulation/ar1.py), [garch.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/simulation/garch.py), [structural_break.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/simulation/structural_break.py) | **100% Direct Reuse** | None. Generates replayable fixed-seed return series. |
| **Conclusion Comparator** | [sensitivity.py](file:///private/tmp/evidence-routed-inference-sharpelab/src/eri/routing/sensitivity.py) | **Direct Reuse with Thin Framing** | Wrapper extracts hurdle decisions into top-level SharpeLab verdict. |
| **Presentation Payload** | `src/eri/demo/sharpelab_adapter.py` | **NEW MODULE** | Formats `AgenticWorkflowState` into JSON structure for UI. |
| **User Interface** | `ui/index.html`, `ui/app.js`, `ui/style.css` | **NEW FRONTEND** | Single-screen HTML/JS/CSS dashboard. |

---

## 9. Scenario Verification Table

Actual numerical outputs were empirically verified inside `/private/tmp/evidence-routed-inference-sharpelab` using Python. The results are summarized below:

| Scenario Name | Config / Seed | $N$ | Diagnostics Produced | Analyst A (Naive IID) Result | Analyst B (HAC / Boot) Result | Eligibility Output | Verdict |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **AR(1) Serial Dependence (Primary)** | `ar1`, seed=4003 | 250 | Ljung-Box $p = 3.0 \times 10^{-6}$ (`contradicts`) | $\hat{SR} = 0.1253$<br>SE = 0.0635<br>CI = **[0.0008, 0.2497]** ($CI_{low} > 0$) | $\hat{SR} = 0.1253$<br>SE = 0.0851 (+34%)<br>CI = **[-0.0415, 0.2921]** ($CI_{low} \le 0$) | Naive IID: `INELIGIBLE`<br>HAC: `ADMISSIBLE`<br>Bootstrap: `ADMISSIBLE` | **`ASSUMPTION-SENSITIVE`** |
| **Volatility Clustering** | `garch`, seed=4202 | 300 | ARCH-LM $p = 4.67 \times 10^{-5}$ (`contradicts`) | $\hat{SR} = 0.1712$<br>SE = 0.0582<br>CI = **[0.0572, 0.2852]** ($CI_{low} > 0$) | $\hat{SR} = 0.1712$<br>SE = 0.0674 (+16%)<br>Boot CI = **[0.0686, 0.2779]** ($CI_{low} > 0$) | Naive IID: `INELIGIBLE`<br>HAC: `ADMISSIBLE`<br>Bootstrap: `ADMISSIBLE` | **`ROBUST`** |
| **Structural Break (Secondary)** | `break`, seed=4303 | 300 | Chow break test (`contradicts`) | $\hat{SR} = 0.2024$<br>SE = 0.0583<br>CI = [0.0881, 0.3167] | All methods fail stationarity | All methods: `INELIGIBLE`<br>`Abstain = True` | **`ABSTAIN`** |

---

## 10. Primary Scenario Recommendation

**Primary Recommendation: AR(1) Serial Dependence (`ar1`, seed=4003, $N=250$, mean=0.004, vol=0.04, $\phi=0.35$)**

- **Why it is recommended over GARCH**:
  Under the built-in GARCH demo (seed 4202), both Naive IID ($CI = [0.057, 0.285]$) and Circular Block Bootstrap ($CI = [0.069, 0.278]$) remain strictly above zero. While eligibility rules rule out IID, both admissible and inadmissible methods agree that Sharpe exceeds zero.
  In contrast, the AR(1) seed 4003 scenario creates a **genuine decision flip**: Naive IID reports a statistically significant positive Sharpe ratio ($CI_{lower} = 0.0008 > 0$), whereas HAC and Bootstrap expand the standard error by +34%, causing the 95% confidence interval to cross zero ($CI_{lower} = -0.0415 \le 0$).

---

## 11. Secondary Abstention Scenario

**Secondary Recommendation: Structural Break (`break`, seed=4303, $N=300$)**

- **Purpose**: Demonstrates automatic system abstention when statistical assumptions collapse entirely.
- **Behavior**: The Chow split-sample diagnostic detects a material shift in population mean/variance ($p < 0.05$). The deterministic policy `abstain_on_structural_instability=True` triggers explicit abstention.
- **Outcome**: `selected_method = None`, `Abstain = True`, Verdict = **`ABSTAIN`**.

---

## 12. Optional Third Scenario

**Optional Third Recommendation: Volatility Clustering (`garch`, seed=4202, $N=300$)**

- **Purpose**: Demonstrates a **ROBUST** verdict where assumptions differ but all admissible specifications reach the same conclusion.
- **Behavior**: ARCH-LM test detects squared-return dependence. Naive IID is ruled `INELIGIBLE`. However, both HAC and Bootstrap confidence intervals remain strictly positive ($CI_{lower} > 0$).
- **Outcome**: Verdict = **`ROBUST`**.

---

## 13. Analyst-Card Construction

The "Two Analysts" card is constructed by taking the single raw return series $y_t$ and running two separate inference evaluations:

1. **Analyst A (Naive IID Gaussian Analyst)**:
   - **Method**: `iid-gaussian-sharpe`
   - **Formulas**: $\hat{SR} = \frac{\bar{y}}{\hat{\sigma}}$, $SE_{IID} = \sqrt{\frac{1 + \frac{1}{2}\hat{SR}^2}{N}}$, $CI = \hat{SR} \pm 1.96 \cdot SE_{IID}$
   - **Assumption**: Returns are independent, identically distributed Gaussian random variables.

2. **Analyst B (Robust Heteroskedastic / HAC Analyst)**:
   - **Method**: `hac-sharpe` (Bartlett / Newey-West)
   - **Formulas**: Uses influence function series $IF_t = \frac{e_t}{\sigma} - \frac{S(e_t^2 - \sigma^2)}{2\sigma^2}$ and Bartlett kernel long-run variance.
   - **Assumption**: Returns exhibit weak dependence / autocorrelation, requiring heteroskedasticity and autocorrelation consistent standard errors.

---

## 14. Evidence Presentation

The Diagnostic Evidence Matrix presents the output of `src/eri/diagnostics/registry.py` as typed cards:

- **Linear Dependence**: Ljung-Box test ($Q$ statistic, $p$-value).
- **Squared Dependence**: ARCH-LM test ($LM$ statistic, $p$-value).
- **Distribution Shape**: Jarque-Bera test (skewness, excess kurtosis, $p$-value).
- **Structural Stability**: Split-sample Chow test (mean shift $z$, variance ratio).
- **Evidence Direction Badges**:
  - `SUPPORTS`: Green badge (assumption holds).
  - `CONTRADICTS`: Red badge (assumption violated).
  - `INCONCLUSIVE`: Gray badge (insufficient statistical power).

---

## 15. Admissibility Presentation

The Admissibility View translates `MethodEligibility` into explicit badges:

- **`ADMISSIBLE (PRIMARY)`**: Selected primary specification (e.g. `hac-sharpe`).
- **`ADMISSIBLE (SENSITIVITY)`**: Qualified sensitivity specification (e.g. `circular-block-bootstrap`).
- **`INELIGIBLE`**: Disqualified specification with explicit auditable reason (e.g. `iid-gaussian-sharpe`: *"Temporal dependence contradicts IID inference."*).
- **`ABSTAIN`**: Disqualified from issuing point estimates due to structural break.

---

## 16. Formal Verdict Definitions

SharpeLab defines three top-level product verdicts:

1. **`ROBUST`**:
   - Primary method is admissible.
   - All admissible sensitivity specifications reach the **same decision** under the frozen decision rule.
   - *Meaning*: The conclusion is invariant to scientifically defensible assumption variations.

2. **`ASSUMPTION-SENSITIVE`**:
   - Primary method is admissible.
   - At least one admissible specification or the naive baseline produces a **different decision** under the frozen decision rule.
   - *Meaning*: The conclusion depends critically on which valid statistical assumptions are made.

3. **`ABSTAIN`**:
   - No primary method satisfies minimum validity conditions (e.g. structural break detected).
   - *Meaning*: Statistical inference is invalid on this sample; issuing a point estimate would be scientifically unsupportable.

---

## 17. Demo Decision-Rule Definition

To avoid undocumented or arbitrary thresholds, the demo freezes one explicit **Demo Decision Rule**:

> **Decision Rule (Benchmark Hurdle):**
> A specification is classified as **exceeding the hurdle** (`PASS`) if and only if its lower 95% confidence interval bound exceeds zero:
> $$\text{Decision}(m) = \begin{cases} \text{PASS} & \text{if } CI_{\text{lower}}(m) > 0.0 \\ \text{FAIL} & \text{if } CI_{\text{lower}}(m) \le 0.0 \end{cases}$$

- In Scenario 1 (`ar1`, seed 4003):
  - Naive IID (Ineligible): $CI = [0.0008, 0.2497] \rightarrow \text{PASS}$
  - HAC (Admissible): $CI = [-0.0415, 0.2921] \rightarrow \text{FAIL}$
  - Bootstrap (Admissible): $CI = [-0.0093, 0.2904] \rightarrow \text{FAIL}$
  - **Result**: Conclusions disagree $\rightarrow$ Verdict = **`ASSUMPTION-SENSITIVE`**.

---

## 18. Audit-Trail Design

The UI includes an collapsible **Audit Trail Drawer** backed directly by `AgenticWorkflowState.audit_events`.
Each entry displays:
- **Event ID & Sequence Number**
- **Actor** (`diagnostic-planner`, `deterministic-core`, `skeptical-reviewer`, `report`)
- **Status** (`accepted`, `rejected`, `vetoed`, `completed`)
- **Payload & Rationale**: Redacted, non-hallucinated audit parameters.

---

## 19. Replay, Mock, and Live Labeling

Every screen and UI element clearly displays execution mode badges:
- **`REPLAY MODE: DETERMINISTIC`**: Indicates fixed-seed synthetic data generation (Seed 4003 / 4303).
- **`AGENT MODE: MOCK (OFFLINE)`**: Indicates Phase 4A agent orchestration running offline without LLM network calls.
- **`ENGINE: DETERMINISTIC CORE`**: Indicates math and admissibility rules were executed by plain Python verification code.

---

## 20. Technology Comparison

Three technology stacks were evaluated for the SharpeLab UI:

| Criteria | Streamlit | FastAPI + Static HTML/JS | Fully Static Replay UI |
| :--- | :--- | :--- | :--- |
| **Rapid Implementation** | High | High | Very High |
| **Visual Polish & Customization** | Low (rigid layout) | **Very High (custom CSS)** | **Very High (custom CSS)** |
| **Offline Reliability** | Medium (Streamlit server state) | High | **100% (zero server needed)** |
| **Direct Python Integration** | High | High | N/A (pre-rendered JSON) |
| **One-Command Startup** | `streamlit run app.py` | `python -m http.server` | `python -m http.server` |
| **Dependency Risk** | Medium (Streamlit version drift) | **Minimal (vanilla JS/CSS)** | **Zero (zero dependencies)** |

---

## 21. Final Technology Recommendation

**Recommendation: FastAPI / Python Static Server + Vanilla HTML/JS/CSS (`ui/`)**

- **Rationale**:
  1. **Zero Node/React build chain**: Eliminates `npm`, `vite`, `webpack`, or Node version mismatches.
  2. **Maximum Visual Polish**: Vanilla CSS allows custom glassmorphic styling, crisp typography, and responsive visual layout without Streamlit's restrictive widget constraints.
  3. **Dual Execution Mode**: Can run either via a lightweight Python static server (`python3 -m http.server`) serving pre-rendered scenario JSONs, or via a 30-line FastAPI endpoint for dynamic replay.
  4. **100% Offline & Deterministic**: Zero external API dependencies.

---

## 22. Proposed File Structure

```text
/private/tmp/evidence-routed-inference-sharpelab/
├── docs/
│   └── sharpelab-hackathon-demo-plan.md     <-- (This planning document)
├── src/
│   └── eri/
│       └── demo/
│           ├── __init__.py
│           ├── sharpelab_adapter.py          <-- Python UI Payload Serializer (~80 LOC)
│           └── sharpelab_cli.py              <-- One-command demo runner script (~40 LOC)
├── ui/
│   ├── index.html                           <-- Single-screen dashboard markup
│   ├── style.css                            <-- Modern dark-mode styling & layout
│   ├── app.js                               <-- Interactive UI state & render logic
│   └── data/
│       ├── ar1_disagreement.json            <-- Pre-rendered Scenario 1 payload
│       ├── garch_robust.json                <-- Pre-rendered Scenario 2 payload
│       └── break_abstain.json               <-- Pre-rendered Scenario 3 payload
└── Makefile                                 <-- `make sharpelab-demo` target
```

---

## 23. Minimum Vertical Slice

The minimum code required to deliver the demo:
1. `src/eri/demo/sharpelab_adapter.py`: Calls `run_agentic_workflow(...)` for seeds 4003, 4202, 4303 and serializes state to JSON.
2. `ui/index.html` + `ui/app.js` + `ui/style.css`: Single-page frontend visualizer.
3. `Makefile`: Target `make sharpelab-demo` which launches a local server and opens `ui/index.html`.

---

## 24. Implementation Sequence

```
Step 1: Write `src/eri/demo/sharpelab_adapter.py`
        └── Test via `tests/unit/test_sharpelab_adapter.py`
Step 2: Generate pre-rendered JSON payloads into `ui/data/`
Step 3: Build HTML/CSS visual layout in `ui/index.html` & `ui/style.css`
Step 4: Connect scenario switcher & interactive state in `ui/app.js`
Step 5: Add `make sharpelab-demo` command to Makefile
Step 6: Verify offline local startup and visual rendering
```

---

## 25. Testing Strategy

1. **Unit Test**: `tests/unit/test_sharpelab_adapter.py`
   - Verifies `build_sharpelab_payload("ar1")` returns non-empty `evidence`, `eligibility`, `analyst_a`, `analyst_b`, and `verdict == "ASSUMPTION-SENSITIVE"`.
   - Verifies `build_sharpelab_payload("break")` returns `verdict == "ABSTAIN"`.
2. **Schema Test**: Validates JSON serialization structure against expected UI schema.
3. **Offline Server Test**: Verifies `python3 -m http.server` serves `ui/index.html` cleanly.

---

## 26. One-Command Startup Plan

```bash
make sharpelab-demo
```

Under the hood, this target executes:
```bash
PYTHONPATH=src .venv/bin/python3 -m eri.demo.sharpelab_cli --open
```
Which launches a local HTTP server at `http://localhost:8080` and opens the browser automatically.

---

## 27. Presentation Fallback

If Python runtime environment issues occur during the live demo:
- **Fallback**: Open `ui/index.html` directly in any web browser using pre-rendered static JSON artifacts in `ui/data/`.
- **Result**: The UI will render with 100% fidelity and interactive scenario switching without requiring Python execution.

---

## 28. Allowed Scientific Claims

The hackathon presentation and documentation are strictly bounded to:
1. "Specialized agents acquire, audit, and critique statistical evidence."
2. "A deterministic core enforces method eligibility and computes uncertainty."
3. "The system abstains when statistical validity conditions are violated."
4. "SharpeLab surfaces implicit assumption failures and tests conclusion robustness across admissible methods."

---

## 29. Prohibited Scientific Claims

The presentation MUST NOT state or imply:
1. ❌ "LLM agents improve statistical estimation accuracy or calibration."
2. ❌ "The system proves universal superiority over traditional risk models."
3. ❌ "Mock execution demonstrates LLM reasoning quality."
4. ❌ "The pilot results prove real-world market performance."
5. ❌ "Every disagreement has one uniquely correct statistical specification."

---

## 30. Risks

| Risk Description | Severity | Mitigation Strategy |
| :--- | :---: | :--- |
| Browser CORS restriction on local `file://` fetch | Medium | Use `python3 -m http.server 8080` or embed static JSON in `data.js`. |
| Presenter misstates agent role as math calculator | Medium | Rehearse script: *“Agents request evidence; deterministic core does the math.”* |
| Python environment path mismatch | Low | Use `.venv/bin/python3` or `PYTHONPATH=src`. |

---

## 31. Unresolved Questions

1. *Should the UI allow custom CSV uploads during the 3-minute pitch?*
   - **Recommendation**: Keep custom CSV upload as an optional tab; rely on fixed-seed pre-packaged scenarios for the 3-minute pitch to guarantee instant execution.

---

## 32. Effort Estimate

- **Backend Adapter (`sharpelab_adapter.py`)**: 1.0 hour
- **Unit Test (`test_sharpelab_adapter.py`)**: 0.5 hours
- **Frontend HTML/CSS/JS (`ui/`)**: 3.5 hours
- **CLI & Makefile Integration**: 0.5 hours
- **Total Implementation Effort**: **5.5 hours**

---
*Plan created in worktree `/private/tmp/evidence-routed-inference-sharpelab` on branch `feature/sharpelab-hackathon-demo`.*
