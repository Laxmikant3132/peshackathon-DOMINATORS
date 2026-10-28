# Human Firewall

Human Firewall is a cybersecurity and digital forensics platform for identifying phishing, scam campaigns, malicious infrastructure, payment fraud, and harmful online behavior. It combines a Python FastAPI threat engine, a modern Next.js dashboard, and a browser extension into one investigative workflow for analysts, security teams, and digital risk monitoring.

## Overview

This project is built to analyze and classify:

- Email phishing attempts and scam indicators
- Suspicious URLs, domains, and website infrastructure
- UPI and payment fraud patterns
- Social abuse, toxic content, and platform threats
- Geolocation and network intelligence tied to suspicious activity
- Browser-based page risk in real time

The platform is split into three layers:

- `backend/` — API, threat analysis logic, forensic services, and classification models
- `frontend/` — dashboard UI built with Next.js and Tailwind CSS
- `extension/` — browser protection layer for page warnings and real-time context checks

## Why this project stands out

Human Firewall is not just a spam filter. It is designed for investigation and evidence-oriented analysis.

It helps users answer questions like:

- Is this message phishing or legitimate?
- Is the sender or domain suspicious?
- What is the likely origin of the traffic?
- Is the infrastructure hosted, proxied, or routed through VPN/TOR services?
- Does a URL or UPI identifier match known scam behavior?
- Is there a broader campaign pattern behind this activity?

## Core features

### 1. Email and phishing forensics
- Email body, subject, sender, and header inspection
- Threat scoring and suspicious-pattern detection
- Authentication checks such as SPF, DKIM, and DMARC review
- Domain mismatch detection against major brands
- Attachment, DNS, and URL-level investigation
- Evidence metadata and forensic reasoning output

### 2. Geolocation and infrastructure intelligence
This is one of the most important features in the platform.

- IP-based geolocation lookup for country, region, city, and timezone
- ASN, ISP, organization, and network type analysis
- Hosting detection and infrastructure classification
- VPN, proxy, TOR, and relay detection flags
- Privacy and anonymity status reporting
- Confidence scoring and provider-level sourcing for better investigation context

These geolocation and network insights help analysts assess whether a suspicious message or threat is tied to a known region, infrastructure provider, or anonymous network path.

### 3. URL, domain, and DNS security analysis
- URL reputation screening
- Suspicious domain and keyword detection
- SSL and domain-age checks
- Typosquatting and impersonation analysis
- DNS and infrastructure investigation for risky links

### 4. UPI and payment scam defense
- UPI fraud detection logic
- Suspicious payment request identification
- Scam keyword and impersonation checks
- Risk scoring for fraud-prone transaction messages

### 5. Social abuse and harmful content monitoring
- Toxic comment and abuse heuristics
- YouTube-related threat and harassment analysis
- Indicator generation for harmful online behavior
- Support for repeated offender and campaign-pattern review

### 6. Threat intelligence and attribution support
- Threat intel correlations
- Domain and campaign-matching indicators
- Evidence-oriented summaries for analyst review
- Graph-based relationship context between suspicious entities

### 7. Browser extension protection
- Real-time page monitoring
- Warning overlays for risky or malicious content
- Quick user-facing alerts from the extension layer
- Lightweight support for browser-based threat checks

## Tech stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, Pandas, NumPy, scikit-learn
- Data and ML: joblib-based models, heuristic rules, and forensic scoring
- Integrations: geolocation APIs, Gmail/YouTube-related services, Firebase, threat intelligence hooks
- Browser: Chrome and Edge extension with JavaScript background logic

## Repository structure

```text
.
├── backend/
│   ├── data/
│   ├── dataset/
│   ├── model/
│   ├── services/
│   ├── tests/
│   ├── app.py
│   ├── main.py
│   ├── threat_engine.py
│   └── requirements.txt
├── extension/
│   ├── _locales/
│   ├── background.js
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── styles.css
│   ├── warning.html
│   └── warning.js
├── frontend/
│   ├── app/
│   ├── components/
│   ├── i18n/
│   ├── lib/
│   ├── messages/
│   ├── services/
│   ├── package.json
│   └── ...
├── README.md
├── run_all.bat
└── .gitignore
```

## Prerequisites

Before running the project, make sure you have:

- Node.js 18+
- npm
- Python 3.9+
- pip
- A Chromium-based browser for extension testing

## Quick start

### 1. Clone the project

```bash
git clone <your-repository-url>
cd HumanFirewall_youtube
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

Run the API:

```bash
uvicorn main:app --reload
```

The backend will be available at:

- http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Set up the frontend

Open a second terminal and run:

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at:

- http://localhost:3000

### 4. Load the extension

1. Open Chrome or Edge
2. Go to `chrome://extensions/`
3. Turn on Developer mode
4. Click Load unpacked
5. Select the `extension/` folder from this repository

## Environment and API configuration

Some features depend on external services and environment variables, including:

- YouTube API keys
- IP geolocation providers
- Firebase configuration
- Threat-intel and provider-backed enrichment services

Example environment variables:

```bash
export YOUTUBE_API_KEY="your_key_here"
export IPINFO_TOKEN="your_token_here"
```

The main backend analysis entry points are in `backend/main.py` and `backend/threat_engine.py`.

## Running the full app

Use two terminals:

- Terminal 1: backend
- Terminal 2: frontend

Then open the dashboard in your browser and use the extension for real-time browser-side checks.

## Development notes

- Backend logic is concentrated in `backend/main.py` and `backend/threat_engine.py`
- Frontend pages live under `frontend/app/`
- Extension logic is split across `extension/background.js`, `popup.js`, and warning pages
- Test files are present under `backend/tests/` and `frontend/tests/`

## Testing

Backend tests:

```bash
cd backend
pytest
```

Frontend tests:

```bash
cd frontend
npx playwright test
```

## License

This project is licensed under the ISC license.

## Mission

Human Firewall is designed to make digital threat investigation more actionable by combining phishing detection, geolocation intelligence, URL analysis, payment-fraud checks, and abusive-content monitoring into a single platform.

