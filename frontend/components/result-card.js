/**
 * frontend/components/result-card.js
 * 
 * Renders individual modality breakdown cards and horizontal progress bars for
 * Text Semantics, URL Lexical Engine, and Brand Alignment.
 * Minimalist light design with Lucide SVG outline icons and restrained status colors.
 */

class ResultCard {
  static renderModalityCards(containerId, analysisData) {
    const container = document.getElementById(containerId);
    if (!container || !analysisData) return;

    const textRes = analysisData.text_analysis || {};
    const urlRes = analysisData.url_analysis || {};
    const contraRes = analysisData.contradiction_analysis || {};

    const textProb = textRes.fraud_probability !== undefined && textRes.fraud_probability !== null 
      ? textRes.fraud_probability * 100 
      : null;
    const urlProb = urlRes.fraud_probability !== null && urlRes.fraud_probability !== undefined 
      ? urlRes.fraud_probability * 100 
      : null;
    const contraScore = contraRes.contradiction_score !== undefined 
      ? contraRes.contradiction_score * 100 
      : 0;

    const getScoreBadge = (probVal) => {
      if (probVal === null) {
        return `<span class="badge-neutral">No input</span>`;
      }
      if (probVal >= 50) return `<span class="badge-high">${probVal.toFixed(1)}% risk</span>`;
      if (probVal >= 25) return `<span class="badge-medium">${probVal.toFixed(1)}% risk</span>`;
      return `<span class="badge-low">${probVal.toFixed(1)}% risk</span>`;
    };

    const getBarColor = (val) => {
      if (val === null || val === undefined) return "#e2e8f0";
      if (val >= 50) return "#ef4444";
      if (val >= 25) return "#f59e0b";
      return "#22c55e";
    };

    const isMismatch = contraRes.brand_mismatch_detected;
    const brandBadge = isMismatch
      ? `<span class="badge-high">Brand mismatch</span>`
      : `<span class="badge-low">Aligned</span>`;

    container.innerHTML = `
      <!-- Horizontal Modality Stack Bars -->
      <div class="modality-meter-stack">
        <div class="meter-row">
          <div class="meter-info">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>SMS Semantics</span>
          </div>
          <div class="meter-track">
            <div class="meter-bar" style="width: ${textProb !== null ? textProb : 0}%; background-color: ${getBarColor(textProb)};"></div>
          </div>
          <div class="meter-val" style="color: ${getBarColor(textProb)};">${textProb !== null ? `${textProb.toFixed(0)}/100` : "—"}</div>
        </div>

        <div class="meter-row">
          <div class="meter-info">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
            </svg>
            <span>URL Lexical Analysis</span>
          </div>
          <div class="meter-track">
            <div class="meter-bar" style="width: ${urlProb !== null ? urlProb : 0}%; background-color: ${getBarColor(urlProb)};"></div>
          </div>
          <div class="meter-val" style="color: ${getBarColor(urlProb)};">${urlProb !== null ? `${urlProb.toFixed(0)}/100` : "—"}</div>
        </div>

        <div class="meter-row">
          <div class="meter-info">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
            <span>Decision Fusion</span>
          </div>
          <div class="meter-track">
            <div class="meter-bar" style="width: ${analysisData.risk_score || 0}%; background-color: ${getBarColor(analysisData.risk_score)};"></div>
          </div>
          <div class="meter-val" style="color: ${getBarColor(analysisData.risk_score)};">${(analysisData.risk_score || 0).toFixed(0)}/100</div>
        </div>
      </div>

      <!-- Detailed Modality Breakdown Box -->
      <div class="modality-container">
        <!-- Text Analysis Section -->
        <div class="modality-section">
          <div class="modality-header">
            <div class="modality-title">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span>SMS content analysis</span>
            </div>
            ${getScoreBadge(textProb)}
          </div>
          <div class="modality-stats">
            <div class="stat-line">
              <span class="stat-label">Urgency index</span>
              <span class="stat-value">${((textRes.urgency_analysis?.urgency_score || 0) * 100).toFixed(0)}%</span>
            </div>
            <div class="stat-line">
              <span class="stat-label">OTP / credential demand</span>
              <span class="stat-value ${textRes.urgency_analysis?.has_otp_request ? 'text-danger' : 'text-muted'}">
                ${textRes.urgency_analysis?.has_otp_request ? "Detected" : "None"}
              </span>
            </div>
            <div class="stat-line">
              <span class="stat-label">Threat keyword matches</span>
              <span class="stat-value">${textRes.urgency_analysis?.matched_keywords?.length || 0} flagged</span>
            </div>
          </div>
        </div>

        <!-- URL Analysis Section -->
        <div class="modality-section">
          <div class="modality-header">
            <div class="modality-title">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
              <span>URL domain verification</span>
            </div>
            ${getScoreBadge(urlProb)}
          </div>
          <div class="modality-stats">
            <div class="stat-line">
              <span class="stat-label">Analyzed domain</span>
              <span class="stat-value mono-val truncate">${urlRes.lexical_features?.Domain || (urlRes.url || "None")}</span>
            </div>
            <div class="stat-line">
              <span class="stat-label">Top-level domain (TLD)</span>
              <span class="stat-value ${urlRes.lexical_features?.IsSuspiciousTLD ? 'text-danger' : ''}">
                .${urlRes.lexical_features?.TLD || "N/A"} ${urlRes.lexical_features?.IsSuspiciousTLD ? "(High risk)" : ""}
              </span>
            </div>
            <div class="stat-line">
              <span class="stat-label">Crawl dependency</span>
              <span class="stat-value text-safe">Zero-crawl (0.15ms)</span>
            </div>
          </div>
        </div>

        <!-- Brand Alignment Section -->
        <div class="modality-section">
          <div class="modality-header">
            <div class="modality-title">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
              <span>Brand similarity check</span>
            </div>
            ${brandBadge}
          </div>
          <div class="modality-stats">
            <div class="stat-line">
              <span class="stat-label">Claimed brand</span>
              <span class="stat-value">${contraRes.detected_brand ? contraRes.detected_brand.charAt(0).toUpperCase() + contraRes.detected_brand.slice(1) : "None claimed"}</span>
            </div>
            <div class="stat-line">
              <span class="stat-label">Subdomain spoofing</span>
              <span class="stat-value ${contraRes.flags?.some(f => f.toLowerCase().includes("subdomain")) ? 'text-warning' : 'text-muted'}">
                ${contraRes.flags?.some(f => f.toLowerCase().includes("subdomain")) ? "Detected" : "None"}
              </span>
            </div>
            <div class="stat-line">
              <span class="stat-label">Contradiction score</span>
              <span class="stat-value">${contraScore.toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

window.ResultCard = ResultCard;
