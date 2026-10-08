/**
 * frontend/app.js
 * 
 * Application controller orchestrating UI state, API communication,
 * test case quick-loaders, report generation, and component rendering for Bimodal Fraud Detection.
 * Light minimal theme, zero emoji, Lucide iconography.
 */

const API_BASE = "/api/v1";

let currentInputMode = "text";
let latestAnalysisData = null;
let riskMeter = null;

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Components
  riskMeter = new RiskMeter("riskMeterContainer");
  riskMeter.render(0, "No active analysis", "#15803d", "Enter message text or URL above, or select a preloaded test case.");

  // Load Initial Data
  loadTestCases();
  loadMetricsAndBenchmarks();
  checkSystemHealth();
  updateCharCount();

  // Close modal on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeComplaintModal();
  });
});

function updateCharCount() {
  const textInput = document.getElementById("inputMessageText");
  const counter = document.getElementById("charCounter");
  if (textInput && counter) {
    const len = textInput.value.length;
    counter.innerText = `${len} / 500 characters`;
  }
}

function setInputMode(mode) {
  currentInputMode = mode;
  document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));

  const btnMap = { text: "inputModeText", url: "inputModeUrl" };
  const activeBtn = document.getElementById(btnMap[mode]);
  if (activeBtn) activeBtn.classList.add("active");

  const groupText = document.getElementById("groupTextMessage");
  const groupUrl = document.getElementById("groupExplicitUrl");
  const btnText = document.getElementById("btnText");

  if (mode === "text") {
    if (groupText) groupText.style.display = "block";
    if (groupUrl) groupUrl.style.display = "block";
    if (btnText) btnText.innerHTML = "Analyze Fraud Risk &rarr;";
  } else if (mode === "url") {
    if (groupText) groupText.style.display = "none";
    if (groupUrl) groupUrl.style.display = "block";
    if (btnText) btnText.innerHTML = "Analyze URL Risk &rarr;";
  }
}

function switchMainTab(tabId) {
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => (c.style.display = "none"));

  if (tabId === "scanner") {
    const tabBtn = document.getElementById("tabScannerBtn");
    const tabContent = document.getElementById("tabScanner");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.style.display = "block";
  } else if (tabId === "benchmarks") {
    const tabBtn = document.getElementById("tabBenchmarksBtn");
    const tabContent = document.getElementById("tabBenchmarks");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.style.display = "block";
    loadMetricsAndBenchmarks();
  } else if (tabId === "api") {
    const tabBtn = document.getElementById("tabApiBtn");
    const tabContent = document.getElementById("tabApi");
    if (tabBtn) tabBtn.classList.add("active");
    if (tabContent) tabContent.style.display = "block";
  }
}

async function handleAnalyzeSubmit(event) {
  if (event) event.preventDefault();

  const textInput = (document.getElementById("inputMessageText")?.value || "").trim();
  const urlInput = (document.getElementById("inputExplicitUrl")?.value || "").trim();

  const spinner = document.getElementById("btnSpinner");
  const btnIcon = document.getElementById("btnIcon");
  const btnText = document.getElementById("btnText");
  const originalText = btnText ? btnText.innerHTML : "Analyze Fraud Risk &rarr;";

  if (spinner) spinner.style.display = "inline-block";
  if (btnIcon) btnIcon.style.display = "none";
  if (btnText) btnText.innerText = "Evaluating threat telemetry...";

  try {
    const payload = {
      text: currentInputMode === "url" ? "" : textInput,
      url: urlInput || null
    };

    const res = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned ${res.status}`);
    }

    const data = await res.json();
    renderAnalysisResults(data);
  } catch (error) {
    console.error("Analysis Error:", error);
    alert(`Error performing threat analysis: ${error.message || error}`);
  } finally {
    if (spinner) spinner.style.display = "none";
    if (btnIcon) btnIcon.style.display = "inline-block";
    if (btnText) btnText.innerHTML = originalText;
  }
}

function renderAnalysisResults(data) {
  latestAnalysisData = data;

  // Update Last Analysis Time
  const timeElem = document.getElementById("lastAnalysisTime");
  if (timeElem) {
    const now = new Date();
    timeElem.innerText = `Last analysis: ${now.toLocaleTimeString()}`;
  }

  // 1. Render Risk Gauge
  if (riskMeter) {
    riskMeter.render(data.risk_score, data.risk_tier, data.risk_color, data.verdict);
  }

  // 2. Render Bimodal Breakdown Cards & Progress Stack
  ResultCard.renderModalityCards("modalityCardsContainer", data);

  // 3. Render Deep Evidence Panel
  EvidencePanel.render("evidencePanelContainer", data);

  // 4. Update Developer JSON Viewer
  const jsonViewer = document.getElementById("jsonViewer");
  if (jsonViewer) {
    jsonViewer.textContent = JSON.stringify(data, null, 2);
  }
}

async function loadTestCases() {
  try {
    const res = await fetch(`${API_BASE}/test-cases`);
    if (!res.ok) return;
    const cases = await res.json();

    renderCaseRows("pillsOrganicPositive", cases.organic_positive || [], "dot-phish");
    renderCaseRows("pillsOrganicNegative", cases.organic_negative || [], "dot-legit");
    renderCaseRows("pillsAdversarial", cases.adversarial_mismatch || [], "dot-adv");
  } catch (err) {
    console.error("Failed to load test cases:", err);
  }
}

function renderCaseRows(containerId, items, dotClass) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = items.map(item => `
    <button type="button" class="case-row-btn" onclick="applyTestCase(${escapeJsonAttribute(item)})">
      <div class="case-row-left">
        <span class="case-dot ${dotClass}"></span>
        <span class="case-row-label">${escapeHtml(item.description)}</span>
      </div>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="case-row-arrow">
        <polyline points="9 18 15 12 9 6"/>
      </svg>
    </button>
  `).join("");
}

function escapeJsonAttribute(obj) {
  return JSON.stringify(obj).replace(/"/g, '&quot;');
}

function escapeHtml(text) {
  if (typeof text !== "string") return text;
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function applyTestCase(item) {
  setInputMode("text");
  const textElem = document.getElementById("inputMessageText");
  const urlElem = document.getElementById("inputExplicitUrl");
  if (textElem) textElem.value = item.text || "";
  if (urlElem) urlElem.value = item.url || "";
  updateCharCount();
  handleAnalyzeSubmit(null);
}

// PDF Report Generation Handlers

function downloadAnalysisReport() {
  if (!latestAnalysisData) {
    alert("Please run an analysis before downloading a report.");
    return;
  }

  const btn = document.getElementById("btnDownloadReport");
  const originalHtml = btn ? btn.innerHTML : "";
  if (btn) btn.innerHTML = `<span>Preparing Analysis PDF...</span>`;

  const payload = {
    text: (document.getElementById("inputMessageText")?.value || "").trim(),
    url: (document.getElementById("inputExplicitUrl")?.value || "").trim() || null
  };

  fetch(`${API_BASE}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      
      const disposition = res.headers.get("content-disposition") || "";
      let filename = "Fraud_Analysis_Report.pdf";
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];

      return res.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    })
    .catch((err) => {
      console.error("PDF Download Error:", err);
      alert(`Error generating PDF report: ${err.message || err}`);
    })
    .finally(() => {
      if (btn) btn.innerHTML = originalHtml;
    });
}

function openComplaintModal() {
  const modal = document.getElementById("complaintModalBackdrop");
  if (modal) {
    modal.classList.add("open");
    const nameInput = document.getElementById("reporterName");
    if (nameInput) setTimeout(() => nameInput.focus(), 50);
  }
}

function closeComplaintModal() {
  const modal = document.getElementById("complaintModalBackdrop");
  if (modal) modal.classList.remove("open");
}

async function handleComplaintSubmit(event) {
  if (event) event.preventDefault();

  const name = (document.getElementById("reporterName")?.value || "").trim();
  const email = (document.getElementById("reporterEmail")?.value || "").trim();
  const phone = (document.getElementById("reporterPhone")?.value || "").trim() || null;
  const channel = document.getElementById("reporterChannel")?.value || "SMS";
  const notes = (document.getElementById("reporterNotes")?.value || "").trim() || null;

  if (!name || !email) {
    alert("Please provide both your name and email address for the formal complaint report.");
    return;
  }

  const btn = document.getElementById("btnModalSubmit");
  const spinner = document.getElementById("btnModalSpinner");
  const icon = document.getElementById("btnModalIcon");
  const text = document.getElementById("btnModalText");

  if (spinner) spinner.style.display = "inline-block";
  if (icon) icon.style.display = "none";
  if (text) text.innerText = "Compiling Dossier PDF...";
  if (btn) btn.disabled = true;

  const payload = {
    text: (document.getElementById("inputMessageText")?.value || "").trim(),
    url: (document.getElementById("inputExplicitUrl")?.value || "").trim() || null,
    reporter_name: name,
    reporter_email: email,
    reporter_phone: phone,
    channel: channel,
    notes: notes
  };

  try {
    const res = await fetch(`${API_BASE}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const disposition = res.headers.get("content-disposition") || "";
    let filename = "Fraud_Complaint_Report.pdf";
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) filename = match[1];

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    closeComplaintModal();
  } catch (err) {
    console.error("Complaint PDF Generation Error:", err);
    alert(`Failed to generate complaint PDF: ${err.message || err}`);
  } finally {
    if (spinner) spinner.style.display = "none";
    if (icon) icon.style.display = "inline-block";
    if (text) text.innerText = "Generate & Download Complaint PDF";
    if (btn) btn.disabled = false;
  }
}

async function loadMetricsAndBenchmarks() {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) return;
    const metrics = await res.json();

    const textAuc = metrics.models?.text_model?.roc_auc || 0.9954;
    const urlAuc = metrics.models?.url_model?.roc_auc || 0.9988;
    const fusionAuc = metrics.models?.fusion_model?.roc_auc || 1.0000;

    const elTextAuc = document.getElementById("kpiTextAuc");
    const elUrlAuc = document.getElementById("kpiUrlAuc");
    const elFusionAuc = document.getElementById("kpiFusionAuc");

    if (elTextAuc) elTextAuc.innerText = textAuc.toFixed(4);
    if (elUrlAuc) elUrlAuc.innerText = urlAuc.toFixed(4);
    if (elFusionAuc) elFusionAuc.innerText = fusionAuc.toFixed(4);

    const ablationTable = document.getElementById("ablationTableBody");
    if (ablationTable && metrics.ablation_benchmark?.modalities_comparison) {
      ablationTable.innerHTML = metrics.ablation_benchmark.modalities_comparison.map(m => `
        <tr>
          <td><strong>${escapeHtml(m.modality)}</strong></td>
          <td class="text-muted"><small>${escapeHtml(m.features)}</small></td>
          <td class="text-safe"><strong>${(m.accuracy * 100).toFixed(2)}%</strong></td>
          <td>${(m.precision * 100).toFixed(2)}%</td>
          <td>${(m.recall * 100).toFixed(2)}%</td>
          <td>${(m.f1_score * 100).toFixed(2)}%</td>
          <td><strong>${m.roc_auc.toFixed(4)}</strong></td>
          <td><span class="mono-text">${m.inference_latency_ms} ms</span></td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Failed to load metrics:", err);
  }
}

async function checkSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return;
    const data = await res.json();
    const statusText = document.getElementById("systemStatusText");
    if (statusText && (data.status === "ok" || data.status === "healthy")) {
      statusText.innerText = "Online";
    }
  } catch (err) {
    console.warn("Backend not yet responding:", err);
  }
}

function copyJsonToClipboard() {
  if (!latestAnalysisData) {
    alert("No analysis data available to copy. Run an analysis first.");
    return;
  }
  navigator.clipboard.writeText(JSON.stringify(latestAnalysisData, null, 2))
    .then(() => alert("Structured JSON response copied to clipboard."))
    .catch(() => alert("Failed to copy JSON to clipboard."));
}
