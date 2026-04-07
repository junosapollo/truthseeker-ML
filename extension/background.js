/**
 * TruthSeeker — Background Service Worker (Manifest V3)
 *
 * Creates a context-menu item "Analyze Truthfulness".
 * When triggered, sends the selected text to the local FastAPI server
 * and forwards the result to the content script for display.
 */

const API_URL = "http://127.0.0.1:8000/analyze";

// ─── Create context menu on install ─────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "truthseeker-analyze",
    title: "🔍 Analyze Truthfulness",
    contexts: ["selection"],
  });
  console.log("[TruthSeeker] Context menu registered.");
});

// ─── Handle context menu clicks ────────────────────────────
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "truthseeker-analyze") return;

  const selectedText = info.selectionText?.trim();
  if (!selectedText) return;

  console.log(`[TruthSeeker] Analyzing: "${selectedText.slice(0, 80)}…"`);

  // Inject the content script if it hasn't been injected yet
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
    await chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      files: ["content.css"],
    });
  } catch (e) {
    // Already injected — fine
  }

  // Show loading state
  chrome.tabs.sendMessage(tab.id, {
    action: "truthseeker-loading",
  });

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: selectedText }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server responded ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log("[TruthSeeker] Result:", data);

    chrome.tabs.sendMessage(tab.id, {
      action: "truthseeker-result",
      payload: data,
    });
  } catch (err) {
    console.error("[TruthSeeker] Error:", err.message);

    chrome.tabs.sendMessage(tab.id, {
      action: "truthseeker-error",
      payload: {
        message:
          err.message.includes("Failed to fetch") ||
          err.message.includes("NetworkError")
            ? "Cannot reach the TruthSeeker API server. Make sure it is running on http://127.0.0.1:8000"
            : err.message,
      },
    });
  }
});
