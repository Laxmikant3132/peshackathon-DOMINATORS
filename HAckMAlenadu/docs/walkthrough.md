# Walkthrough: Phase 3 Foundation - Unbreakable Dataset Generation

This document explains the structure, logic, and identifying patterns of the **Sentinel AI Cyber Attack Simulation Engine**. The dataset is designed to be 100% deterministic, correlation-ready, and production-grade.

## 📊 Dataset Metrics
- **Total Logs**: 1,000 (Hard-Stopped)
- **Distribution**: 70% Normal (700) / 30% Attack (300)
- **Clock**: Strictly monotonic UTC timestamps with no collisions.
- **Layers**: Cross-layer (Endpoint + Network) linked via `session_id`.

## 🛡️ How to Identify Attacks Visually

### 1. Chain 1: Brute Force → Successful Login → Data Exfiltration
This is a standard multi-stage compromise flow.
- **Identify via Session ID**: Look for `attack_x` sessions that appear in both `endpoint_logs.json` and `network_logs.json`.
- **Step-by-Step Flow**:
    1.  **Multiple Fails**: 5–10 Endpoint logs with `action: "login"` and `status: "failed"`.
    2.  **Success**: 1 Endpoint log with `status: "success"`.
    3.  **The Leak**: 1 Network log with `severity_hint: "high"`, `bytes_transferred > 1MB`, and `ip_type: "external"`.

### 2. Chain 2: C2 Beaconing → Lateral Movement
This simulates a persistent threat acting on a schedule.
- **Identify via Timing**: Look for a "heartbeat" pattern in the network logs.
- **Step-by-Step Flow**:
    1.  **Fixed Heartbeat**: 8 Network logs with **exactly 30.0s intervals**.
    2.  **Locked Target**: All events share the same `dst_ip: "45.33.2.1"`.
    3.  **Lateral Movement**: Same `session_id` and `user` logging into multiple different `system` IDs (e.g., `workstation-02`, `fileserver-01`).

### 3. False Positive: Admin Backup
This tests the detection engine's ability to handle high-volume legitimate traffic.
- **Identify via Context**: Session ID prefix `fp_`.
- **Characteristics**:
    - **Volume**: >1MB transfer (resembles exfiltration).
    - **Status**: Labeled `normal`.
    - **Metadata**: Linked to an admin `file_access` log to provide behavioral context for normal behavior.

## 🧠 Correlation Strategy (for Phase 4)
The `session_id` is the primary key for stateful correlation. 
- **Rule-Based**: Alert when a `login: success` is followed by high-volume traffic in the *same* session.
- **ML-Based**: Detect the statistical anomaly of the 30.0s interval "heartbeat" against the random noise of normal traffic.
- **Explainability**: Using the `event_id` sequence, we can reconstruct the full attack narrative from initial brute-force attempt to final data theft.

> [!IMPORTANT]
> The `ip_type` is a derived feature: `internal` logs represent east-west or internal-initiated traffic, while `external` IPs represent the egress/ingress points. Every high-severity exfiltration is guaranteed to be directed to an `external` IP.

## 🛠️ Verification Report
The generation process automatically executes an **Unbreakable Validation Suite**:
- [x] **Distribution**: Verified 70/30 split.
- [x] **Timing**: Verified 0.0s drift on C2 intervals.
- [x] **Integrity**: Verified 0 broken chains across all attack sessions.
- [x] **Uniqueness**: Verified 0 session ID collisions.
