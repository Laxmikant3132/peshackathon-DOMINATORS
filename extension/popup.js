// popup.js for URL Analyser Extension

document.addEventListener("DOMContentLoaded", async () => {
  // Localization
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    const message = chrome.i18n.getMessage(key);
    if (message) el.textContent = message;
  });

  const statusValue = document.getElementById("status-value");
  const urlText = document.getElementById("url-text");
  const scanBtn = document.getElementById("scan-btn");

  // Get current active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url) {
    urlText.textContent = tab.url;
  }

  scanBtn.addEventListener("click", async () => {
    if (!tab || !tab.url) return;

    // Prevent scanning internal browser pages
    if (tab.url.startsWith("chrome://") || tab.url.startsWith("edge://") || tab.url.startsWith("about:")) {
      statusValue.textContent = "System Page (Protected)";
      statusValue.className = "status-value safe";
      return;
    }
    
    scanBtn.disabled = true;
    scanBtn.innerHTML = `<div class="loader"></div><span>${chrome.i18n.getMessage("scanning")}</span>`;
    statusValue.textContent = chrome.i18n.getMessage("scanning");
    
    try {
      const response = await fetch("https://humanfirewall-backend.onrender.com/api/classify-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: tab.url }),
      });

      const data = await response.json();
      
      if (data.safety === "safe") {
        statusValue.textContent = chrome.i18n.getMessage("safeLink");
        statusValue.className = "status-value safe";
      } else if (data.safety === "suspicious") {
        statusValue.textContent = chrome.i18n.getMessage("suspiciousDetected");
        statusValue.className = "status-value suspicious";
      } else {
        statusValue.textContent = chrome.i18n.getMessage("phishingDetected");
        statusValue.className = "status-value danger";
      }
      
    } catch (error) {
      statusValue.textContent = chrome.i18n.getMessage("backendOffline");
      statusValue.className = "status-value danger";
      console.error("Connection error:", error);
    } finally {
      scanBtn.disabled = false;
      scanBtn.textContent = chrome.i18n.getMessage("scanPage");
    }
  });
});
