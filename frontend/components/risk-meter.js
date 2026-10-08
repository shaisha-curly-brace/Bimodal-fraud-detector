/**
 * frontend/components/risk-meter.js
 * 
 * Clean, flat 3-stop SVG risk gauge meter for light theme.
 * Solid colors (green, amber, red), crisp needle, zero glow/neon artifacts.
 */

class RiskMeter {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
  }

  render(score = 0, tier = "No active analysis", color = "#15803d", verdict = "Enter SMS message or URL to evaluate threat risk") {
    if (!this.container) return;

    // Normalize score to 0..100
    const clampedScore = Math.max(0, Math.min(100, Number(score) || 0));

    // Map score (0 to 100) to gauge angle (-90deg to +90deg)
    const angle = -90 + (clampedScore / 100) * 180;

    // Pick 3-stop status color (25 / 50 threshold)
    let statusColor = "#15803d"; // Low / Safe
    if (clampedScore >= 50) {
      statusColor = "#b91c1c"; // High / Hazardous
    } else if (clampedScore >= 25) {
      statusColor = "#b45309"; // Medium / Suspicious
    }

    this.container.innerHTML = `
      <div class="risk-gauge-wrapper">
        <svg viewBox="0 0 240 135" class="gauge-svg" aria-label="Risk score gauge: ${clampedScore} of 100">
          <defs>
            <linearGradient id="riskScaleGradientLight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#16a34a" />
              <stop offset="30%" stop-color="#16a34a" />
              <stop offset="50%" stop-color="#d97706" />
              <stop offset="70%" stop-color="#dc2626" />
              <stop offset="100%" stop-color="#dc2626" />
            </linearGradient>
          </defs>
          
          <!-- Background Track Arc -->
          <path d="M 24 118 A 96 96 0 0 1 216 118" fill="none" stroke="#e2e8f0" stroke-width="10" stroke-linecap="round" />
          
          <!-- 3-Stop Gradient Arc (Green -> Amber -> Red) -->
          <path d="M 24 118 A 96 96 0 0 1 216 118" fill="none" stroke="url(#riskScaleGradientLight)" stroke-width="10" stroke-linecap="round" />
          
          <!-- Gauge Threshold Tick Marks -->
          <!-- 25% (angle -45deg) -->
          <line x1="52" y1="50" x2="48" y2="46" stroke="#cbd5e1" stroke-width="2" />
          <!-- 50% (angle 0deg) -->
          <line x1="120" y1="22" x2="120" y2="16" stroke="#cbd5e1" stroke-width="2" />
          <!-- 75% (angle +45deg) -->
          <line x1="188" y1="50" x2="192" y2="46" stroke="#cbd5e1" stroke-width="2" />

          <!-- Needle Indicator -->
          <g transform="translate(120, 118) rotate(${angle})" class="needle-assembly">
            <line x1="0" y1="0" x2="0" y2="-82" stroke="#0f172a" stroke-width="2.5" stroke-linecap="round" />
            <circle cx="0" cy="0" r="5" fill="#0f172a" />
            <circle cx="0" cy="0" r="2" fill="#ffffff" />
          </g>
        </svg>

        <div class="gauge-details">
          <div class="gauge-score-row">
            <span class="gauge-score-value">${clampedScore.toFixed(0)}</span>
            <span class="gauge-score-denom">/100</span>
          </div>
          <div class="gauge-status-label" style="color: ${statusColor};">
            ${tier}
          </div>
          <p class="gauge-verdict-text">${verdict}</p>
        </div>
      </div>
    `;
  }
}

window.RiskMeter = RiskMeter;
