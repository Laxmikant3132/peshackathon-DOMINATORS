// background.js for URL Analyser Extension

const API_URL = "https://humanfirewall-backend.onrender.com/api/classify-url";

// Keep track of URLs that the user has already allowed
let allowedUrls = new Set();
// Keep track of URLs currently being analysed to avoid duplicate requests
let beingAnalysed = new Set();

// Load allowed URLs from storage on startup
chrome.storage.local.get(["allowedUrls"], (result) => {
  if (result.allowedUrls) {
    allowedUrls = new Set(result.allowedUrls);
  }
});

// Using webNavigation for more robust interception
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
  // Only check top-level frames
  if (details.frameId !== 0) return;

  const url = details.url;

  // Skip internal, local, and already allowed URLs
  if (!url || 
      (!url.startsWith("http://") && !url.startsWith("https://")) ||
      url.includes(chrome.runtime.id) ||
      url.includes("humanfirewall-backend.onrender.com") ||
      url.includes("127.0.0.1") ||
      url.includes("chrome://") ||
      url.includes("edge://") ||
      url.includes("about:")) {
    return;
  }

  // Check if already allowed
  const isAllowed = Array.from(allowedUrls).some(allowed => url.startsWith(allowed));
  if (isAllowed) return;

  // Avoid duplicate analysis for the same URL in a short window
  if (beingAnalysed.has(url)) return;
  beingAnalysed.add(url);
  setTimeout(() => beingAnalysed.delete(url), 5000);

  console.log("Analysing URL:", url);

  // Set badge to indicate scanning
  chrome.action.setBadgeText({ text: "...", tabId: details.tabId });
  chrome.action.setBadgeBackgroundColor({ color: "#00ffff", tabId: details.tabId });

  // Call backend API for analysis
  fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: url }),
  })
  .then(response => {
    if (!response.ok) throw new Error("API not reachable");
    return response.json();
  })
  .then(data => {
    console.log("Analysis Result:", data);
    
    // Clear badge
    chrome.action.setBadgeText({ text: "", tabId: details.tabId });

    if (data && (data.safety === "dangerous" || data.safety === "suspicious")) {
      // Set danger badge
      chrome.action.setBadgeText({ text: "!", tabId: details.tabId });
      chrome.action.setBadgeBackgroundColor({ color: "#ff4d4d", tabId: details.tabId });

      // Block/Redirect to a warning page
      const warningUrl = chrome.runtime.getURL(`warning.html?url=${encodeURIComponent(url)}&safety=${data.safety}&confidence=${data.confidence}&indicators=${encodeURIComponent(JSON.stringify(data.indicators))}`);
      chrome.tabs.update(details.tabId, { url: warningUrl });
    }
  })
  .catch(error => {
    console.warn("URL Analysis failed or skipped:", error.message);
    chrome.action.setBadgeText({ text: "", tabId: details.tabId });
  });
});

// Listen for messages from the warning page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "allowUrl") {
    allowedUrls.add(request.url);
    // Persist to storage
    chrome.storage.local.set({ allowedUrls: Array.from(allowedUrls) });
    // Redirect back to the original URL
    if (sender.tab) {
      chrome.tabs.update(sender.tab.id, { url: request.url });
    }
  }
  return true;
});
