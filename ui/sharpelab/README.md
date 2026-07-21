# Evidence-Routed Inference // SharpeLab Visual Explorer

> **AI that reasons explicitly about scientific assumptions.**

**SharpeLab** is the first interactive demonstration of **Evidence-Routed Inference (ERI)**—a framework that shifts automated reasoning from black-box LLM calculations to explicit, auditable, evidence-governed assumption routing.

---

## The 6-Act Demonstration Flow

1. **Act 1 — The Mystery**: *Can two honest experts reach opposite conclusions from the same data?*
2. **Act 2 — The Conflict**: *Same return data ($N=250$). Same Sharpe estimate ($0.1253$). Opposite conclusions.*
3. **Act 3 — The Evidence**: *Plain-language diagnostic evidence hierarchy (Finding $\rightarrow$ Implication $\rightarrow$ Technical diagnostic).*
4. **Act 4 — Scientific Reasoning**: *Deterministic admissibility table & policy routing guardrails.*
5. **Act 5 — Scientific Verdict**: *Auditable verdict (**Sensitive to assumptions**, **Robust**, or **Cannot conclude**).*
6. **Act 6 — General Principle**: *Extending Evidence-Routed Inference beyond finance to clinical trials, econometrics, psychology, and climate science.*

---

## Local Offline Execution

This UI is a **100% offline, static web page** that loads pre-generated, byte-reproducible JSON artifacts from the deterministic ERI engine.

### Quick Launch:
```bash
make sharpelab-demo
```
- Open browser: **`http://localhost:8080/ui/sharpelab/index.html`**
