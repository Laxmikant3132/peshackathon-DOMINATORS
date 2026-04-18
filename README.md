# 🛡️ Sentinel AI / Human Firewall

**Human Firewall (Sentinel AI Platform)** is an enterprise-grade cybersecurity platform that fuses a sophisticated AI-powered threat detection engine with live network monitoring, endpoint metrics tracking, and real-time inbox scanning. Together with an integrated training platform, it protects organizations from phishing attacks, malware, data exfiltration, lateral movement, and social engineering.

## ✨ Overview

Sentinel AI Platform operates through a **Hybrid Detection Engine** orchestrating multiple micro-sensors. It taps into underlying operating system metrics, active network connections, and integrated OAuth email workflows to catch threats the moment they emerge. Combined with our War Room capability, SOC analysts have complete visibility over endpoint security and data leaks.

## 🚀 Core Features

### 👁️ **Sentinel AI Monitoring & Live Telemetry**
- **Endpoint Threat Telemetry**: Direct integration with system kernels via `psutil` to track high-risk security tools (Mimikatz, Nmap, Wireshark, etc.) and anomalous resource spikes (CPU/RAM).
- **Network Traffic Forensics**: Deep tracking of network sockets to analyze IP beaconing, lateral movement patterns, bulk data exfiltration, and Typosquatting.
- **Machine Learning Flow Analysis**: Network logs are fed directly into a pre-trained `joblib` Random Forest/Neural model that classifies flows and triggers 95%+ confidence alerts based on established malicious datasets.

### 📧 **Real-Time Inbox Scanner**
- **Automated 2-Second Polling**: Real-time integration with Gmail APIs allowing the platform to analyze mail units automatically. No manual refreshes required.
- **AI Phishing Identification**: Scans incoming payloads, snippets, headers, and subjects against known heuristic manipulation tactics and NLP algorithms.
- **Immediate Threat Quarantine**: Automatically flags messages as **Suspicious** or **Dangerous** and provides analysts with raw reporting tools to cybercrime agencies.

### 👥 **Interactive Security War Room**
- **Live Event Feed**: WebSockets stream network and endpoint events instantly into a graphical Command Center.
- **Automated IP Blocking**: Analysts can one-click block suspicious IPs dynamically.
- **Browser-level System Notifications**: Critical alerts (Confidence > 0.90) push directly natively through the browser while operating in the background.

### 🎓 **Security Training & Posture Dashboard**
- **Immersive Phishing Simulations**: Hands-on exercises that guide employees through identifying manipulation.
- **Organizational Posture Analytics**: Granular dashboards showcasing the organization's current threat level, total telemetry pools, and intercepted threats.

## 🧠 Architecture Overview

Our architecture splits the workload into an ultra-fast Next.js edge frontend and a highly concurrent Python FastAPI Threat Engine.

### 1. **Next.js 14 Frontend**
- **TypeScript & TailwindCSS**: Utilizing strict type-safety and modern utility classes.
- **Framer Motion**: Smooth entry/exit animations for critical system alerts.
- **React Context Pipeline `(MonitoringContext)`**: Seamless abstraction of WebSockets, `localStorage` state syncing, and browser notifications to ensure background scripts run unhindered across tabs.

### 2. **FastAPI + ML Threat Engine (`threat_engine.py`)**
- **Asynchronous Data Pumps**: Utilizing `asyncio` to pump hundreds of simulated and live network/endpoint events per second.
- **Hybrid Categorization**:
  - *Heuristic Models*: Brute Force thresholds, Beaconing timing analysis, and Exfiltration volume sensors.
  - *ML Models*: Feature engineering on `dataset_resumido.csv` patterns for exact classification.
- **WebSocket Emitters**: Broadcasts actionable intelligence to active dashboards without polling overhead.

## 🛠️ Technology Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Framer Motion, Lucide React |
| **Backend** | Python 3.9+, FastAPI, Uvicorn, Psutil, WebSockets |
| **Machine Learning** | Scikit-learn, Pandas, Joblib (Network Flow Models) |
| **Cloud & Auth** | Firebase Authentication, Google Workspace (Gmail API), Firestore |

## 📦 Installation & Setup

### Prerequisites
- **Node.js**: v18.0.0+
- **Python**: v3.9+ 
- **Google Cloud Console Account**: For Gmail API OAuth Credentials
- **Firebase Project**: Configured for Web, Auth, and Firestore

### 1. Repository Setup
```bash
git clone https://github.com/your-username/humanfirewall.git
cd humanfirewall
```

### 2. Environment Configuration
Create a `.env.local` to map your backend and Firebase configurations.
```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_id
```

### 3. Start Backend Threat Engine (FastAPI)
The backend acts as the AI analysis node and system monitor.
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```
*The backend runs on `http://localhost:8000`*

### 4. Start Next.js Frontend
```bash
# Return to root directory
npm install
npm run dev
```
*The frontend is accessible at `http://localhost:3000`*

## 🤖 How the Threat Simulation Works

Since production endpoints are rarely actively attacked while debugging, Sentinel contains a built-in `TrafficSimulator`.
- **Endpoint Sensors**: Rapidly sweeps local `psutil` tasks. If you launch `nmap.exe` or `wireshark.exe` locally, Sentinel will flag it as a HIGH_RISK_TOOL in real time.
- **Network Sensors**: Logs active ports and cross-references them against large bulk data transfers.
- **Injections**: Inject Brute Force or Exfiltration attack packets via the Admin Panel to see the AI immediately intercept and categorize the threat.

## 🔒 Security Best Practices Utilized
- **Aggressive Auto-Polling Isolation**: Utilizes strict timestamp cache-busting `(&t=Date.now())` preventing aggressive browser optimization from caching stale email payloads.
- **Event Debouncing**: WebSocket emitters bundle logs into 200ms payload chunks to prevent React DOM lockups during "traffic bursts".
- **Token Handling**: Silent background refresh of Gmail OAuth tokens mapped strictly to Firestore without exposing to component boundaries.

## 📄 License & Compliance
This project enforces robust data-handling principles and targets compliance with modern GDPR strictures regarding PII in system logs. Licensed under the **ISC License**.

---
**🛡️ Sentinel AI / Human Firewall**  
*Next-generation endpoint visualization and zero-day threat interception.*
