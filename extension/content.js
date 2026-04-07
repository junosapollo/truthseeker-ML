/**
 * TruthSeeker — Content Script
 *
 * Renders a floating overlay on the active page showing
 * the misinformation analysis result.
 */

(() => {
  // Prevent double-injection
  if (window.__truthseekerInjected) return;
  window.__truthseekerInjected = true;

  const OVERLAY_ID = "truthseeker-overlay";

  // ─── Remove any existing overlay ─────────────────────────
  function removeOverlay() {
    const existing = document.getElementById(OVERLAY_ID);
    if (existing) existing.remove();
  }

  // ─── Build the overlay container ─────────────────────────
  function createOverlay() {
    removeOverlay();

    const overlay = document.createElement("div");
    overlay.id = OVERLAY_ID;
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-label", "TruthSeeker Analysis Result");

    document.body.appendChild(overlay);
    return overlay;
  }

  // ─── Render: Loading ─────────────────────────────────────
  function showLoading() {
    const overlay = createOverlay();
    overlay.innerHTML = `
      <div class="ts-card ts-loading">
        <div class="ts-header">
          <span class="ts-logo">🔍</span>
          <span class="ts-title">TruthSeeker</span>
          <button class="ts-close" aria-label="Close">&times;</button>
        </div>
        <div class="ts-body">
          <div class="ts-spinner"></div>
          <p class="ts-status-text">Analyzing text…</p>
        </div>
      </div>
    `;
    overlay.querySelector(".ts-close").addEventListener("click", removeOverlay);
  }

  // ─── Render: Result ──────────────────────────────────────
  function showResult(data) {
    const overlay = createOverlay();
    const score = data.truth_score;
    const classification = data.classification;
    const snippet = data.text_snippet || "";

    // Choose accent color based on classification
    const isReal = classification === "Real";
    const accentClass = isReal ? "ts-real" : "ts-fake";
    const emoji = isReal ? "✅" : "⚠️";
    const ringColor = isReal
      ? `conic-gradient(#22c55e ${score}%, #1e293b ${score}%)`
      : `conic-gradient(#ef4444 ${score}%, #1e293b ${score}%)`;

    overlay.innerHTML = `
      <div class="ts-card ${accentClass}">
        <div class="ts-header">
          <span class="ts-logo">🔍</span>
          <span class="ts-title">TruthSeeker</span>
          <button class="ts-close" aria-label="Close">&times;</button>
        </div>
        <div class="ts-body">
          <div class="ts-ring-wrapper">
            <div class="ts-ring" style="background: ${ringColor};">
              <div class="ts-ring-inner">
                <span class="ts-score">${score.toFixed(1)}%</span>
              </div>
            </div>
          </div>
          <p class="ts-classification">${emoji} Likely <strong>${classification}</strong></p>
          <p class="ts-snippet">"${snippet.length > 120 ? snippet.slice(0, 120) + "…" : snippet}"</p>
        </div>
        <div class="ts-footer">
          <span class="ts-badge ${accentClass}">${classification.toUpperCase()}</span>
          <span class="ts-powered">Powered by TruthSeeker AI</span>
        </div>
      </div>
    `;
    overlay.querySelector(".ts-close").addEventListener("click", removeOverlay);

    // Auto-dismiss after 15 seconds
    setTimeout(() => {
      const el = document.getElementById(OVERLAY_ID);
      if (el) {
        el.classList.add("ts-fade-out");
        setTimeout(removeOverlay, 400);
      }
    }, 15000);
  }

  // ─── Render: Error ───────────────────────────────────────
  function showError(msg) {
    const overlay = createOverlay();
    overlay.innerHTML = `
      <div class="ts-card ts-error">
        <div class="ts-header">
          <span class="ts-logo">🔍</span>
          <span class="ts-title">TruthSeeker</span>
          <button class="ts-close" aria-label="Close">&times;</button>
        </div>
        <div class="ts-body">
          <p class="ts-error-icon">❌</p>
          <p class="ts-error-text">${msg}</p>
        </div>
      </div>
    `;
    overlay.querySelector(".ts-close").addEventListener("click", removeOverlay);
  }

  // ─── Message Listener ────────────────────────────────────
  chrome.runtime.onMessage.addListener((message, _sender, _sendResponse) => {
    switch (message.action) {
      case "truthseeker-loading":
        showLoading();
        break;
      case "truthseeker-result":
        showResult(message.payload);
        break;
      case "truthseeker-error":
        showError(message.payload.message);
        break;
    }
  });
})();
