# Evidence-Routed Inference // Demo Video Storyboard

> **Resolution**: 1080p (1920x1080, 60fps)  
> **Total Duration**: 180 Seconds (3:00 Minutes)  
> **Local Server URL**: `http://localhost:8080/ui/sharpelab/index.html`

---

## Scene 1: The Framework & Mystery
- **Timestamp**: `0:00 – 0:25`
- **Duration**: 25 Seconds
- **Screen State**: Initial page load. Header displays *Evidence-Routed Inference: AI that reasons explicitly about scientific assumptions*. Act 1 Mystery Box visible.
- **Click / Action**: Mouse hovers near the *Investigate* button.
- **Narration**: *"Standard AI tools and statistical software calculate answers under hidden, unverified assumptions. When data violate those assumptions, software fails silently—leading honest experts to reach opposite conclusions from identical data. We built Evidence-Routed Inference—an AI architecture that makes scientific assumptions explicit, testable, and auditable."*
- **Visual Focus**: Zoom on brand title and mystery question: *"Can two honest experts reach opposite conclusions from the same data?"*

---

## Scene 2: SharpeLab Introduction
- **Timestamp**: `0:25 – 0:45`
- **Duration**: 20 Seconds
- **Screen State**: Act 1 Mystery Box centered.
- **Click / Action**: None (cursor moves to *Investigate* button).
- **Narration**: *"To demonstrate this framework, we built SharpeLab. In financial quantitative research, the Sharpe ratio measures return per unit of risk. Standard software computes confidence intervals assuming returns are independent and identically distributed. Let's see what happens when that implicit assumption breaks."*
- **Visual Focus**: Highlight *SharpeLab — Interactive Demonstration* tag.

---

## Scene 3: The Conflict & Reveal
- **Timestamp**: `0:45 – 1:55`
- **Duration**: 70 Seconds
- **Screen State**: Act 2 (The Conflict) revealed showing Analyst A (Naive IID) vs Analyst B (HAC).
- **Click / Action**:  
  1. At `0:45`: Click **[ INVESTIGATE ]** button.  
  2. At `1:15`: Click **[ REVEAL HIDDEN ASSUMPTION ]** button.
- **Narration**: *"Notice the conflict: Same return data. Same point estimate of zero-point-one-two-five-three. But Analyst A concludes the performance is statistically positive, while Analyst B concludes it is uncertain. The disagreement is not about the arithmetic—it is about how uncertainty is modeled. We click Reveal hidden assumption. The diagnostic engine detects serial dependence with a Ljung-Box p-value of three times ten to the minus six. The framework rules the naive independence model Not scientifically admissible. Once dependence-aware robust methods are used, the confidence interval crosses zero. The apparent finding disappears when the inadmissible assumption is removed."*
- **Visual Focus**: Highlight Analyst cards, then jump to Act 3 Evidence Matrix and Act 5 Verdict Banner (**Sensitive to assumptions**).

---

## Scene 4: Robust Outcome
- **Timestamp**: `1:55 – 2:15`
- **Duration**: 20 Seconds
- **Screen State**: User clicks *Robust under volatility* tab.
- **Click / Action**: At `1:55`, click **[ Robust under volatility ]** tab.
- **Narration**: *"What if the evidence rejects independence due to volatility clustering instead? Under our second scenario, the engine detects ARCH effects and rules Naive IID inadmissible. However, every scientifically admissible robust method—both HAC and block bootstrap—still confirms the interval is strictly above zero. The verdict is Robust."*
- **Visual Focus**: Green Verdict Banner (**Robust**) and Confidence Interval Visualizer.

---

## Scene 5: Structural Break & Abstention
- **Timestamp**: `2:15 – 2:35`
- **Duration**: 20 Seconds
- **Screen State**: User clicks *Cannot conclude* tab.
- **Click / Action**: At `2:15`, click **[ Cannot conclude ]** tab.
- **Narration**: *"Under our third scenario, the diagnostic engine detects a structural mean break mid-sample. Evaluating a single full-sample Sharpe ratio is scientifically incoherent when the underlying process shifts. Instead of forcing an ungrounded answer, the system explicitly abstains: Cannot conclude."*
- **Visual Focus**: Red Regime Break Visual Strip and Red Verdict Banner (**Cannot conclude**).

---

## Scene 6: Architecture & Broader Relevance
- **Timestamp**: `2:35 – 2:55`
- **Duration**: 20 Seconds
- **Screen State**: Scroll down to Act 6 (Beyond Finance: A General Architecture).
- **Click / Action**: Smooth scroll down.
- **Narration**: *"SharpeLab demonstrates finance, but the architecture is general. Wherever scientific findings depend on hidden assumptions—whether in clinical trials, econometrics, psychology, or climate science—Evidence-Routed Inference ensures conclusions are tested against admissible evidence rules."*
- **Visual Focus**: Grid of 4 domain cards (Clinical Trials, Econometrics, Psychology, Climate Science).

---

## Scene 7: Closing
- **Timestamp**: `2:55 – 3:00`
- **Duration**: 5 Seconds
- **Screen State**: Bottom of page centered on closing statement.
- **Click / Action**: Freeze frame.
- **Narration**: *"Evidence-Routed Inference: Making scientific assumptions explicit. Thank you."*
- **Visual Focus**: Final line: *Evidence-Routed Inference — Making scientific assumptions explicit.*

---

## Storyboard Duration Verification Table

| Scene # | Scene Description | Start Time | End Time | Duration (s) |
| :--- | :--- | :--- | :--- | :--- |
| **Scene 1** | Framework & Mystery | 0:00 | 0:25 | 25s |
| **Scene 2** | SharpeLab Intro | 0:25 | 0:45 | 20s |
| **Scene 3** | Conflict & Sensitive Verdict | 0:45 | 1:55 | 70s |
| **Scene 4** | Robust Outcome | 1:55 | 2:15 | 20s |
| **Scene 5** | Cannot Conclude Outcome | 2:15 | 2:35 | 20s |
| **Scene 6** | Architecture & Broader Relevance | 2:35 | 2:55 | 20s |
| **Scene 7** | Closing | 2:55 | 3:00 | 5s |
| **TOTAL** | **Full Demo Video** | **0:00** | **3:00** | **180s** |
