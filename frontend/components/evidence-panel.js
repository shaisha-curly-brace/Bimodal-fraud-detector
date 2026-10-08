/**
 * frontend/components/evidence-panel.js
 * 
 * Deep forensic evidence breakdown panel rendering highlighted message tokens,
 * lexical URL anatomy table, structured evidence cards, security recommendations,
 * and the conditional "Download Report" button (Complaint vs Analysis).
 * Minimalist light design, 100% Lucide outline SVG icons, zero emoji.
 */

class EvidencePanel {
  static render(containerId, analysisData) {
    const container = document.getElementById(containerId);
    if (!container || !analysisData) return;

    const explanation = analysisData.explanation || {};
    const evidenceItems = explanation.evidence_items || [];
    const recommendations = explanation.recommendations || [];
    const tokens = analysisData.text_analysis?.tokens || [];
    const lex = analysisData.url_analysis?.lexical_features;
    const isHighThreat = analysisData.risk_score >= 50;
    const isMediumThreat = analysisData.risk_score >= 25 && analysisData.risk_score < 50;

    const getSeverityBadge = (severity) => {
      const s = (severity || "").toUpperCase();
      if (s === "CRITICAL" || s === "HIGH") {
        return `<span class="badge-high">${s}</span>`;
      }
      if (s === "MEDIUM") {
        return `<span class="badge-medium">${s}</span>`;
      }
      return `<span class="badge-neutral">${s || "INFO"}</span>`;
    };

    container.innerHTML = `
      <div class="evidence-wrapper">
        <!-- Summary Verdict Banner with Conditional Download Button -->
        <div class="verdict-banner ${isHighThreat ? 'banner-danger' : isMediumThreat ? 'banner-warning' : 'banner-safe'}">
          <div class="banner-content-left">
            <div class="banner-icon">
              ${isHighThreat ? `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              ` : isMediumThreat ? `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
              ` : `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="m9 12 2 2 4-4"/>
                </svg>
              `}
            </div>
            <div class="banner-body">
              <div class="banner-title">Security assessment summary</div>
              <div class="banner-description">${escapeHtml(explanation.summary || "Analysis completed.")}</div>
            </div>
          </div>

          <!-- Report Download Action -->
          <div class="banner-actions">
            ${isHighThreat ? `
              <button type="button" class="btn-report btn-report-danger" onclick="openComplaintModal()" id="btnDownloadReport">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="12" y1="18" x2="12" y2="12"/>
                  <line x1="9" y1="15" x2="15" y2="15"/>
                </svg>
                <span>Download Complaint Report</span>
              </button>
            ` : `
              <button type="button" class="btn-report btn-report-neutral" onclick="downloadAnalysisReport()" id="btnDownloadReport">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                <span>Download Analysis Report</span>
              </button>
            `}
          </div>
        </div>

        <!-- Token Inspector -->
        ${tokens.length > 0 ? `
          <div class="evidence-card">
            <div class="evidence-card-header">
              <div class="evidence-card-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="4 7 4 4 20 4 20 7"/>
                  <line x1="9" y1="20" x2="15" y2="20"/>
                  <line x1="12" y1="4" x2="12" y2="20"/>
                </svg>
                <span>Text token classification</span>
              </div>
              <div class="token-legend">
                <span class="legend-item"><span class="legend-chip token-urgent"></span> Urgency indicator</span>
                <span class="legend-item"><span class="legend-chip token-financial"></span> Credential / Account</span>
                <span class="legend-item"><span class="legend-chip token-url"></span> Extracted URL</span>
              </div>
            </div>
            <div class="token-flow">
              ${tokens.map(t => `<span class="token-tag token-${t.type}">${escapeHtml(t.token)}</span>`).join(" ")}
            </div>
          </div>
        ` : ''}

        <!-- Forensic Factors List -->
        <div class="evidence-card">
          <div class="evidence-card-header">
            <div class="evidence-card-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
                <line x1="3" y1="6" x2="3.01" y2="6"/>
                <line x1="3" y1="12" x2="3.01" y2="12"/>
                <line x1="3" y1="18" x2="3.01" y2="18"/>
              </svg>
              <span>Forensic evidence factors (${evidenceItems.length} evaluated)</span>
            </div>
          </div>
          <div class="factor-list">
            ${evidenceItems.map(item => `
              <div class="factor-item">
                <div class="factor-header">
                  <span class="factor-name">${escapeHtml(item.title)}</span>
                  ${getSeverityBadge(item.severity)}
                </div>
                <div class="factor-text">${escapeHtml(item.description)}</div>
                <div class="factor-meta">Domain: ${escapeHtml(item.category)}</div>
              </div>
            `).join("")}
          </div>
        </div>

        <!-- URL Lexical Anatomy Table (if URL present) -->
        ${lex ? `
          <div class="evidence-card">
            <div class="evidence-card-header">
              <div class="evidence-card-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="2" y1="12" x2="22" y2="12"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                <span>URL lexical anatomy (zero-crawl structural analysis)</span>
              </div>
            </div>
            <div class="table-container">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Extracted value</th>
                    <th>Structural interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Registered domain</td>
                    <td class="mono-text">${escapeHtml(lex.Domain || "None")}</td>
                    <td>${lex.IsDomainIP ? '<span class="text-danger font-medium">Direct IP address (evasion pattern)</span>' : '<span class="text-muted">Standard DNS domain hierarchy</span>'}</td>
                  </tr>
                  <tr>
                    <td>Shannon entropy</td>
                    <td class="mono-text">${lex.Entropy} bits</td>
                    <td>${lex.Entropy > 4.2 ? '<span class="text-danger font-medium">High randomness (possible DGA or obfuscated token)</span>' : '<span class="text-muted">Normal natural lexical entropy</span>'}</td>
                  </tr>
                  <tr>
                    <td>Character continuation rate</td>
                    <td class="mono-text">${(lex.CharContinuationRate * 100).toFixed(1)}%</td>
                    <td>${lex.CharContinuationRate > 0.3 ? '<span class="text-warning font-medium">High continuous alphanumeric run</span>' : '<span class="text-muted">Normal distribution</span>'}</td>
                  </tr>
                  <tr>
                    <td>Protocol scheme</td>
                    <td class="mono-text">${lex.IsHTTPS ? "HTTPS" : "HTTP"}</td>
                    <td>${lex.IsHTTPS ? '<span class="text-muted">TLS transport configured</span>' : '<span class="text-warning font-medium">Unencrypted HTTP connection</span>'}</td>
                  </tr>
                  <tr>
                    <td>Obfuscated characters</td>
                    <td class="mono-text">${lex.NoOfObfuscatedChar} characters</td>
                    <td>${lex.HasObfuscation ? '<span class="text-danger font-medium">Percent-encoding or hex disguise detected</span>' : '<span class="text-muted">Clean string without encoding masking</span>'}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        ` : ''}

        <!-- Recommendations -->
        ${recommendations.length > 0 ? `
          <div class="evidence-card">
            <div class="evidence-card-header">
              <div class="evidence-card-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="m9 12 2 2 4-4"/>
                </svg>
                <span>Recommended response actions</span>
              </div>
            </div>
            <ul class="recommendation-list">
              ${recommendations.map(r => `
                <li>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span>${escapeHtml(r)}</span>
                </li>
              `).join("")}
            </ul>
          </div>
        ` : ''}
      </div>
    `;
  }
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

window.EvidencePanel = EvidencePanel;
