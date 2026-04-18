// warning.js for URL Analyser Extension

// Localization
document.querySelectorAll("[data-i18n]").forEach(el => {
  const key = el.getAttribute("data-i18n");
  const message = chrome.i18n.getMessage(key);
  if (message) el.textContent = message;
});

// Extract URL parameters
const params = new URLSearchParams(window.location.search);
const url = params.get("url");
const safety = params.get("safety");
const confidence = params.get("confidence");
const indicators = JSON.parse(decodeURIComponent(params.get("indicators") || "[]"));

// Set content
document.getElementById("url-text").textContent = url;
document.getElementById("status").textContent = safety === "suspicious" ? chrome.i18n.getMessage("suspiciousDetected") : chrome.i18n.getMessage("phishingDetected");
document.getElementById("confidence").textContent = `${confidence}%`;

const indicatorsContainer = document.getElementById("indicators-container");
indicators.forEach(indicator => {
  const span = document.createElement("span");
  span.className = "indicator";
  span.textContent = indicator;
  indicatorsContainer.appendChild(span);
});

// Event listeners
document.getElementById("btn-back").addEventListener("click", () => {
  // Go back to the previous page or just close the tab if we can't
  if (window.history.length > 1) {
    window.history.back();
  } else {
    window.close();
  }
});

document.getElementById("btn-allow").addEventListener("click", () => {
  // Tell the background script to allow this URL and redirect back
  chrome.runtime.sendMessage({ action: "allowUrl", url: url });
  // Wait a moment for background to process and then redirect
  setTimeout(() => {
    window.location.href = url;
  }, 100);
});
