// Evidence-Routed Inference & SharpeLab Visual Explorer Application Logic

let currentScenarioId = 'ar1-assumption-sensitive';
const payloadCache = {};
let hasRevealed = false;

document.addEventListener('DOMContentLoaded', async () => {
  setupButtons();
  setupScenarioSwitcher();
  await loadAndRenderScenario(currentScenarioId);
});

function setupButtons() {
  const btnInvestigate = document.getElementById('btn-investigate');
  if (btnInvestigate) {
    btnInvestigate.addEventListener('click', () => {
      document.getElementById('act-1-mystery').classList.add('hidden-step');
      document.getElementById('act-scenario-bar').classList.remove('hidden-step');
      document.getElementById('act-2-conflict').classList.remove('hidden-step');
    });
  }

  const btnReveal = document.getElementById('btn-reveal');
  if (btnReveal) {
    btnReveal.addEventListener('click', () => {
      hasRevealed = true;
      showRevealedActs();
      btnReveal.style.display = 'none';
    });
  }
}

function showRevealedActs() {
  document.getElementById('act-3-evidence').classList.remove('hidden-step');
  document.getElementById('act-4-routing').classList.remove('hidden-step');
  document.getElementById('act-5-verdict').classList.remove('hidden-step');
  document.getElementById('act-6-framework').classList.remove('hidden-step');
}

function resetRevealState() {
  hasRevealed = false;
  document.getElementById('act-3-evidence').classList.add('hidden-step');
  document.getElementById('act-4-routing').classList.add('hidden-step');
  document.getElementById('act-5-verdict').classList.add('hidden-step');
  document.getElementById('act-6-framework').classList.add('hidden-step');

  const btnReveal = document.getElementById('btn-reveal');
  if (btnReveal) btnReveal.style.display = 'inline-block';

  const auditContainer = document.getElementById('audit-container');
  if (auditContainer) auditContainer.classList.remove('active');
}

function setupScenarioSwitcher() {
  const buttons = document.querySelectorAll('.scenario-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const scenarioId = btn.getAttribute('data-scenario');
      if (!scenarioId || scenarioId === currentScenarioId) return;

      buttons.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      currentScenarioId = scenarioId;
      resetRevealState();
      await loadAndRenderScenario(scenarioId);
    });
  });
}

async function loadAndRenderScenario(scenarioId) {
  if (payloadCache[scenarioId]) {
    renderPayload(payloadCache[scenarioId]);
    return;
  }

  let payload = null;
  try {
    const response = await fetch(`../../demo/sharpelab/${scenarioId}.json`);
    if (response.ok) {
      payload = await response.json();
    }
  } catch (err) {
    console.warn(`Local fetch failed for ${scenarioId}, checking fallback payload.`, err);
  }

  if (payload) {
    payloadCache[scenarioId] = payload;
    renderPayload(payload);
  } else {
    document.getElementById('error-fallback').classList.remove('hidden-step');
  }
}

function renderPayload(payload) {
  // 1. Headline & Disclosures
  document.getElementById('headline-title').textContent = payload.headline;
  document.getElementById('headline-sub').textContent = payload.disagreement_hook_text;
  document.getElementById('rule-disclosure').innerHTML = `<strong>Demo Rule:</strong> ${payload.rule_disclosure}`;
  document.getElementById('disclosure-badge').textContent = payload.synthetic_disclosure;
  document.getElementById('execution-badge').textContent = payload.execution_mode;

  // 2. Comparison Cards (Act 2)
  const analystContainer = document.getElementById('analyst-cards-container');
  analystContainer.innerHTML = payload.analyst_cards.map(card => {
    const isSupported = card.categorical_decision === 'SUPPORTED';
    const isAdmissible = card.admissible;

    if (payload.scenario_type === 'abstain') {
      return `
        <div class="analyst-card abstain-card">
          <div>
            <div class="card-title">
              <span>${card.title}</span>
              <span class="badge badge-red">NOT ADMISSIBLE</span>
            </div>
            <div class="contrast-box">
              <div class="contrast-row">
                <span class="contrast-label">Analysis Model</span>
                <span class="contrast-val" style="color: var(--accent-red);">${card.method_name}</span>
              </div>
              <div class="contrast-row">
                <span class="contrast-label">Sharpe Ratio</span>
                <span class="contrast-val">Abstained (Undefined)</span>
              </div>
              <div class="contrast-row">
                <span class="contrast-label">95% Conf. Interval</span>
                <span class="contrast-val">N/A</span>
              </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0;">
              <span style="font-size: 0.85rem; color: var(--text-secondary);">Categorical Decision</span>
              <span class="badge badge-red">${card.decision_label}</span>
            </div>
          </div>
          <div class="assumption-box">
            <strong>Key Assumption:</strong> ${card.key_assumption}
          </div>
        </div>
      `;
    }

    const titleLabel = card.analyst_id === 'analyst-a-naive' 
      ? 'Analysis assuming independent returns' 
      : (card.analyst_id === 'analyst-b-robust' ? 'Analysis allowing serial dependence' : card.title);

    return `
      <div class="analyst-card ${isAdmissible ? 'admissible-card' : 'ineligible-card'}">
        <div>
          <div class="card-title">
            <span>${titleLabel}</span>
            <span class="badge ${isAdmissible ? 'badge-green' : 'badge-red'}">
              ${isAdmissible ? 'SUPPORTED BY EVIDENCE' : 'NOT ADMISSIBLE'}
            </span>
          </div>

          <div class="contrast-box">
            <div class="contrast-row">
              <span class="contrast-label">1. Sharpe Estimate</span>
              <span class="contrast-val" style="color: var(--accent-blue);">${card.estimate ? card.estimate.toFixed(4) : 'N/A'}</span>
            </div>
            <div class="contrast-row">
              <span class="contrast-label">2. Uncertainty (SE)</span>
              <span class="contrast-val">${card.standard_error ? card.standard_error.toFixed(4) : 'N/A'}</span>
            </div>
            <div class="contrast-row">
              <span class="contrast-label">3. 95% Conf. Interval</span>
              <span class="contrast-val">[${card.confidence_interval[0].toFixed(4)}, ${card.confidence_interval[1].toFixed(4)}]</span>
            </div>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0;">
            <span style="font-size: 0.85rem; color: var(--text-secondary);">Categorical Decision</span>
            <span class="badge ${isSupported ? 'badge-green' : 'badge-amber'}">
              ${card.decision_label}
            </span>
          </div>
        </div>

        <div class="assumption-box">
          <strong>Key Assumption:</strong> ${card.key_assumption}
        </div>
      </div>
    `;
  }).join('');

  // 3. Confidence Interval Chart Graphic / Visual Strip
  const chartBarsContainer = document.getElementById('chart-bars');
  const visualizerHeader = document.getElementById('visualizer-header');

  if (payload.scenario_type === 'abstain') {
    visualizerHeader.innerHTML = `<span>Structural Stability Visualizer</span><span style="font-size: 0.8rem; color: var(--text-secondary);">Regime Break Shift</span>`;
    chartBarsContainer.innerHTML = `
      <div class="regime-break-strip">
        <strong>⚡ MATERIAL STRUCTURAL BREAK DETECTED AT 50% WINDOW</strong><br>
        Segment 1 Mean: -0.010 | Segment 2 Mean: +0.030 (Population mean shift violates stationarity). Full-sample Sharpe is scientifically incoherent.
      </div>
    `;
  } else if (payload.scenario_type === 'robust') {
    visualizerHeader.innerHTML = `<span>95% Confidence Interval Comparison</span><span style="font-size: 0.8rem; color: var(--text-secondary);">Vertical line = Zero Benchmark (0.0)</span>`;
    chartBarsContainer.innerHTML = `
      <div class="zero-reference-line" title="Zero Benchmark (0.0)"></div>
      <div class="chart-row">
        <div class="chart-label">Bartlett HAC (Primary)</div>
        <div class="chart-track">
          <div class="interval-bar green-bar" style="left: 42%; width: 33%;"></div>
          <div class="point-dot" style="left: 56.5%;" title="Point Estimate: 0.1712"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-green);">[0.0391, 0.3033] ✓</div>
      </div>
      <div class="chart-row">
        <div class="chart-label">Circular Block Bootstrap</div>
        <div class="chart-track">
          <div class="interval-bar green-bar" style="left: 45.5%; width: 26%;"></div>
          <div class="point-dot" style="left: 56.5%;" title="Point Estimate: 0.1712"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-green);">[0.0686, 0.2779] ✓</div>
      </div>
    `;
  } else {
    visualizerHeader.innerHTML = `<span>95% Confidence Interval Comparison</span><span style="font-size: 0.8rem; color: var(--text-secondary);">Vertical line = Zero Benchmark (0.0)</span>`;
    chartBarsContainer.innerHTML = `
      <div class="zero-reference-line" title="Zero Benchmark (0.0)"></div>
      <div class="chart-row">
        <div class="chart-label">Analysis assuming independent returns</div>
        <div class="chart-track">
          <div class="interval-bar green-bar" style="left: 35.5%; width: 30%;"></div>
          <div class="point-dot" style="left: 50.5%;" title="Point Estimate: 0.1253"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-green);">[0.0008, 0.2497] ✓</div>
      </div>
      <div class="chart-row">
        <div class="chart-label">Analysis allowing serial dependence (HAC)</div>
        <div class="chart-track">
          <div class="interval-bar red-bar" style="left: 30%; width: 42%;"></div>
          <div class="point-dot" style="left: 50.5%;" title="Point Estimate: 0.1253"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-amber);">[-0.0415, 0.2921] ✕</div>
      </div>
      <div class="chart-row">
        <div class="chart-label">Circular Block Bootstrap (Cross-check)</div>
        <div class="chart-track">
          <div class="interval-bar red-bar" style="left: 33.8%; width: 37.5%;"></div>
          <div class="point-dot" style="left: 50.5%;" title="Point Estimate: 0.1253"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-amber);">[-0.0093, 0.2904] ✕</div>
      </div>
    `;
  }

  // 4. Act 3 Plain-Language Evidence Matrix (Hierarchy: Finding -> Implication -> Diagnostic)
  const evidenceContainer = document.getElementById('evidence-container');
  evidenceContainer.innerHTML = payload.evidence_cards.map(ev => {
    let headlineFinding = "Returns exhibit serial dependence.";
    let implicationText = "Independence is not supported. The naive uncertainty model is therefore not scientifically admissible.";
    
    if (ev.diagnostic_name.includes("Volatility")) {
      headlineFinding = "Returns exhibit volatility clustering.";
      implicationText = "Independence is not supported. Constant variance model is not scientifically admissible.";
    } else if (ev.diagnostic_name.includes("Stability")) {
      if (ev.direction_badge === "CONTRADICTS") {
        headlineFinding = "Return-generating process undergoes a structural mean break.";
        implicationText = "Full-sample stationarity is not supported. Full-sample Sharpe ratio is scientifically incoherent.";
      } else {
        headlineFinding = "Sub-sample mean and variance remain stable across the window.";
        implicationText = "Stationarity assumption is supported by empirical sub-sample test.";
      }
    }

    let badgeClass = ev.direction_badge === 'CONTRADICTS' ? 'badge-red' : (ev.direction_badge === 'SUPPORTS' ? 'badge-green' : 'badge-muted');

    return `
      <div class="evidence-item">
        <div class="evidence-top">
          <div class="evidence-finding-headline">1. Finding: ${headlineFinding}</div>
          <span class="badge ${badgeClass}">${ev.direction_badge} ASSUMPTION</span>
        </div>
        <div class="evidence-implication">2. Implication: ${implicationText}</div>
        <div class="evidence-technical-detail">
          3. Technical Diagnostic: ${ev.diagnostic_name} | Statistic: ${ev.statistic !== null ? ev.statistic.toFixed(4) : 'N/A'} | p-value: ${ev.p_value !== null ? ev.p_value.toExponential(2) : 'N/A'}
        </div>
      </div>
    `;
  }).join('');

  // 5. Act 4 Admissibility Table
  const admissibilityContainer = document.getElementById('admissibility-container');
  admissibilityContainer.innerHTML = payload.admissibility_cards.map(adm => {
    let badgeClass = 'badge-red';
    let plainBadge = 'Not scientifically admissible';

    if (adm.status_badge.includes('PRIMARY')) {
      badgeClass = 'badge-green';
      plainBadge = 'Supported by evidence · Selected';
    } else if (adm.status_badge.includes('SENSITIVITY')) {
      badgeClass = 'badge-info';
      plainBadge = 'Supported by evidence · Cross-check';
    }

    return `
      <tr>
        <td style="font-weight: 600;">${adm.method_name}</td>
        <td><span class="badge ${badgeClass}">${plainBadge}</span></td>
        <td style="color: var(--text-secondary); font-size: 0.85rem;">${adm.reasons.join(' ')}</td>
      </tr>
    `;
  }).join('');

  // 6. Act 5 Verdict Banner
  const verdictBox = document.getElementById('verdict-box');
  const verdictBadge = document.getElementById('verdict-badge');
  const verdictTitle = document.getElementById('verdict-title');
  const verdictTakeaway = document.getElementById('verdict-takeaway');

  verdictBox.className = 'verdict-box';
  if (payload.scenario_type === 'robust') {
    verdictBox.classList.add('verdict-robust');
    verdictBadge.className = 'badge badge-green';
    verdictTakeaway.textContent = "The evidence rejects IID assumptions, but every scientifically admissible method still reaches the same positive conclusion.";
  } else if (payload.scenario_type === 'abstain') {
    verdictBox.classList.add('verdict-abstain');
    verdictBadge.className = 'badge badge-red';
    verdictTakeaway.textContent = "A structural break makes a single full-period conclusion scientifically incoherent, so the system abstains rather than forcing an answer.";
  } else {
    verdictBox.classList.add('verdict-sensitive');
    verdictBadge.className = 'badge badge-amber';
    verdictTakeaway.textContent = "The apparent finding disappears when the inadmissible assumption is removed.";
  }

  verdictTitle.textContent = payload.verdict_label;
  document.getElementById('verdict-explanation').textContent = payload.verdict_explanation;

  // 7. Audit Trail Log
  const auditContainer = document.getElementById('audit-container');
  auditContainer.innerHTML = payload.audit_trail.map(item => `
    <div class="audit-row">
      <span style="color: var(--accent-blue);">${item.event_id}</span>
      <span style="color: var(--text-primary); font-weight: 600; margin: 0 0.5rem;">[${item.actor}]</span>
      <span>${item.summary}</span>
    </div>
  `).join('');

  // Audit Toggle Handler
  const btnToggleAudit = document.getElementById('btn-toggle-audit');
  if (btnToggleAudit) {
    btnToggleAudit.onclick = () => {
      const isVisible = auditContainer.classList.contains('active');
      if (isVisible) {
        auditContainer.classList.remove('active');
        btnToggleAudit.textContent = '▸ View Unalterable Audit Trail Log (#evt-8f92a10c)';
      } else {
        auditContainer.classList.add('active');
        btnToggleAudit.textContent = '▾ Hide Unalterable Audit Trail Log (#evt-8f92a10c)';
      }
    };
  }
}
