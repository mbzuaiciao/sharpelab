# Evidence-Routed Inference // 3-Minute Live Presentation Script

> **Target Duration**: 2:45 to 3:00 (180 Seconds Total)  
> **Presenter**: Live Hackathon Demonstrator  
> **Interface**: `http://localhost:8080/ui/sharpelab/index.html`

---

## Script & Timing Breakdown

### Segment 1 — Broad Problem & Framework (0:00 – 0:25 | 25 Seconds)
- **Visual**: Screen shows top header: **Evidence-Routed Inference: AI that reasons explicitly about scientific assumptions**, and Act 1 Mystery Box.
- **Narration**:  
  "Standard AI tools and statistical software calculate answers under hidden, unverified assumptions. When data violate those assumptions, software fails silently—leading honest experts to reach opposite conclusions from identical data. We built *Evidence-Routed Inference*—an AI architecture that makes scientific assumptions explicit, testable, and auditable."

---

### Segment 2 — SharpeLab & Sharpe Ratio Context (0:25 – 0:45 | 20 Seconds)
- **Visual**: Focus on *SharpeLab — Interactive Demonstration* tag and the initial mystery question.
- **Narration**:  
  "To demonstrate this framework, we built *SharpeLab*. In financial quantitative research, the Sharpe ratio measures return per unit of risk. Standard software computes confidence intervals assuming returns are independent and identically distributed. Let's see what happens when that implicit assumption breaks."

---

### Segment 3 — The Primary Scenario: Sensitive to Assumptions (0:45 – 1:55 | 70 Seconds)
- **Action**: Click **[ INVESTIGATE ]** button.
- **Visual**: Act 1 collapses. Act 2 (The Conflict) appears showing Analyst A ($CI = [0.0008, 0.2497]$, Supported) vs Analyst B ($CI = [-0.0415, 0.2921]$, Not Supported).
- **Narration**:  
  "Notice the conflict: Same return data. Same point estimate of zero-point-one-two-five-three. But Analyst A concludes the performance is statistically positive, while Analyst B concludes it is uncertain. The disagreement is not about the arithmetic—it is about how uncertainty is modeled."

- **Action**: Click **[ REVEAL HIDDEN ASSUMPTION ]** button.
- **Visual**: Acts 3, 4, 5, and 6 appear. Act 3 shows plain-language evidence (*Returns exhibit serial dependence*), Act 4 shows Admissibility Router, Act 5 shows **Sensitive to assumptions** verdict.
- **Narration**:  
  "We click *Reveal hidden assumption*. The diagnostic engine detects serial dependence with a Ljung-Box p-value of three times ten to the minus six. The framework rules the naive independence model *Not scientifically admissible*. Once dependence-aware robust methods are used, the confidence interval crosses zero. The apparent finding disappears when the inadmissible assumption is removed."

---

### Segment 4 — Scenario 2: Robust Under Volatility (1:55 – 2:15 | 20 Seconds)
- **Action**: Click **[ Robust under volatility ]** tab on the scenario switcher bar.
- **Visual**: Cards update instantly to GARCH(1,1) volatility clustering scenario. Verdict banner turns GREEN: **Robust**.
- **Narration**:  
  "What if the evidence rejects independence due to volatility clustering instead? Under our second scenario, the engine detects ARCH effects and rules Naive IID inadmissible. However, every scientifically admissible robust method—both HAC and block bootstrap—still confirms the interval is strictly above zero. The verdict is *Robust*."

---

### Segment 5 — Scenario 3: Cannot Conclude (2:15 – 2:35 | 20 Seconds)
- **Action**: Click **[ Cannot conclude ]** tab on the scenario switcher bar.
- **Visual**: Cards update to Structural Break scenario. Red Regime Break Visual Strip appears. Verdict banner turns RED: **Cannot conclude**.
- **Narration**:  
  "Under our third scenario, the diagnostic engine detects a structural mean break mid-sample. Evaluating a single full-sample Sharpe ratio is scientifically incoherent when the underlying process shifts. Instead of forcing an ungrounded answer, the system explicitly abstains: *Cannot conclude*."

---

### Segment 6 — Architecture & Broader Relevance (2:35 – 2:55 | 20 Seconds)
- **Visual**: Scroll to Act 6 (Beyond Finance: A General Architecture).
- **Narration**:  
  "SharpeLab demonstrates finance, but the architecture is general. Wherever scientific findings depend on hidden assumptions—whether in clinical trials, econometrics, psychology, or climate science—Evidence-Routed Inference ensures conclusions are tested against admissible evidence rules."

---

### Segment 7 — Closing (2:55 – 3:00 | 5 Seconds)
- **Visual**: Final line highlighted: *Evidence-Routed Inference — Making scientific assumptions explicit.*
- **Narration**:  
  "Evidence-Routed Inference: Making scientific assumptions explicit. Thank you."

---

## Arithmetic Verification of Timing

$$\text{Total Duration} = 25\text{s} + 20\text{s} + 70\text{s} + 20\text{s} + 20\text{s} + 20\text{s} + 5\text{s} = 180\text{ Seconds (Exactly 3:00 Minutes)}$$
