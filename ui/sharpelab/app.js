// SharpeLab Visual Explorer Application Logic

let currentScenarioId = 'ar1-assumption-sensitive';
const payloadCache = {};

document.addEventListener('DOMContentLoaded', async () => {
  setupScenarioSwitcher();
  await loadAndRenderScenario(currentScenarioId);
});

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

function resetRevealState() {
  document.getElementById('section-evidence').classList.add('hidden-step');
  document.getElementById('section-admissibility').classList.add('hidden-step');
  document.getElementById('section-verdict').classList.add('hidden-step');
  const btnReveal = document.getElementById('btn-reveal');
  if (btnReveal) btnReveal.style.display = 'inline-block';
  
  const auditContainer = document.getElementById('audit-container');
  if (auditContainer) auditContainer.classList.remove('active');
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
  // 1. Headline & Hook Text
  document.getElementById('headline-title').textContent = payload.headline;
  document.getElementById('headline-sub').textContent = payload.disagreement_hook_text;
  document.getElementById('rule-disclosure').innerHTML = `<strong>Demo Rule:</strong> ${payload.rule_disclosure}`;

  document.getElementById('disclosure-badge').textContent = payload.synthetic_disclosure;
  document.getElementById('execution-badge').textContent = payload.execution_mode;

  // 2. Analyst / Specification Comparison Cards
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
                <span class="contrast-label">Estimator Status</span>
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

    return `
      <div class="analyst-card ${isAdmissible ? 'admissible-card' : 'ineligible-card'}">
        <div>
          <div class="card-title">
            <span>${card.title}</span>
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

  // 3. Interval Comparison Graphic / Regime Break Visual Strip
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
    // Sensitive scenario chart
    visualizerHeader.innerHTML = `<span>95% Confidence Interval Comparison</span><span style="font-size: 0.8rem; color: var(--text-secondary);">Vertical line = Zero Benchmark (0.0)</span>`;
    chartBarsContainer.innerHTML = `
      <div class="zero-reference-line" title="Zero Benchmark (0.0)"></div>
      <div class="chart-row">
        <div class="chart-label">Naive IID Gaussian</div>
        <div class="chart-track">
          <div class="interval-bar green-bar" style="left: 35.5%; width: 30%;"></div>
          <div class="point-dot" style="left: 50.5%;" title="Point Estimate: 0.1253"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-green);">[0.0008, 0.2497] ✓</div>
      </div>
      <div class="chart-row">
        <div class="chart-label">Bartlett HAC (Primary)</div>
        <div class="chart-track">
          <div class="interval-bar red-bar" style="left: 30%; width: 42%;"></div>
          <div class="point-dot" style="left: 50.5%;" title="Point Estimate: 0.1253"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-amber);">[-0.0415, 0.2921] ✕</div>
      </div>
      <div class="chart-row">
        <div class="chart-label">Circular Block Bootstrap</div>
        <div class="chart-track">
          <div class="interval-bar red-bar" style="left: 33.8%; width: 37.5%;"></div>
          <div class="point-dot" style="left: 50.5%;" title="Point Estimate: 0.1253"></div>
        </div>
        <div class="chart-stat" style="color: var(--accent-amber);">[-0.0093, 0.2904] ✕</div>
      </div>
    `;
  }

  // 4. Diagnostic Evidence Matrix
  const evidenceContainer = document.getElementById('evidence-container');
  evidenceContainer.innerHTML = payload.evidence_cards.map(ev => {
    let badgeClass = 'badge-muted';
    let badgeText = ev.direction_badge;
    if (ev.direction_badge === 'CONTRADICTS') {
      badgeClass = 'badge-red';
      badgeText = 'CONTRADICTS ASSUMPTION';
    }
    if (ev.direction_badge === 'SUPPORTS') {
      badgeClass = 'badge-green';
      badgeText = 'SUPPORTS ASSUMPTION';
    }

    return `
      <div class="evidence-item">
        <div class="evidence-top">
          <span class="evidence-name">${ev.diagnostic_name}</span>
          <span class="badge ${badgeClass}">${badgeText}</span>
        </div>
        <div class="evidence-desc">${ev.interpretation}</div>
        <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem;">
          Statistic: ${ev.statistic !== null ? ev.statistic.toFixed(4) : 'N/A'} | p-value: ${ev.p_value !== null ? ev.p_value.toExponential(2) : 'N/A'}
        </div>
      </div>
    `;
  }).join('');

  // 5. Admissibility Table
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

  // 6. Verdict Banner
  const verdictBox = document.getElementById('verdict-box');
  const verdictBadge = document.getElementById('verdict-badge');
  const verdictTitle = document.getElementById('verdict-title');

  verdictBox.className = 'verdict-box';
  if (payload.scenario_type === 'robust') {
    verdictBox.classList.add('verdict-robust');
    verdictBadge.className = 'badge badge-green';
  } else if (payload.scenario_type === 'abstain') {
    verdictBox.classList.add('verdict-abstain');
    verdictBadge.className = 'badge badge-red';
  } else {
    verdictBox.classList.add('verdict-sensitive');
    verdictBadge.className = 'badge badge-amber';
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

  // 8. Reveal Button Handler
  const btnReveal = document.getElementById('btn-reveal');
  if (btnReveal) {
    btnReveal.onclick = () => {
      document.getElementById('section-evidence').classList.remove('hidden-step');
      document.getElementById('section-admissibility').classList.remove('hidden-step');
      document.getElementById('section-verdict').classList.remove('hidden-step');
      btnReveal.style.display = 'none';

      document.getElementById('section-evidence').scrollIntoView({ behavior: 'smooth' });
    };
  }

  // 9. Audit Toggle Handler
  const btnToggleAudit = document.getElementById('btn-toggle-audit');
  if (btnToggleAudit) {
    btnToggleAudit.onclick = () => {
      const isVisible = auditContainer.classList.contains('active');
      if (isVisible) {
        auditContainer.classList.remove('active');
        btnToggleAudit.textContent = '▸ View Audit Trail Log (#evt-8f92a10c)';
      } else {
        auditContainer.classList.add('active');
        btnToggleAudit.textContent = '▾ Hide Audit Trail Log (#evt-8f92a10c)';
      }
    };
  }
}
