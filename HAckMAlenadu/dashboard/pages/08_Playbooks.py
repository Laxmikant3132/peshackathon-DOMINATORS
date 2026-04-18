import streamlit as st
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header

# --- PAGE CONFIG ---
st.set_page_config(page_title="SENTINEL AI | Playbooks", layout="wide")
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()

processor = bridge.get_processor()

st.title("🧩 SOAR PLAYBOOKS & RESPONSE ENGINE")
st.markdown("<small>Actionable automation and manual containment playbooks</small>", unsafe_allow_html=True)
st.markdown("---")

incidents = list(processor.incident_gen.active_incidents.values())

if not incidents:
    st.success("No active threats requiring containment. All playbooks on standby.")
else:
    target_inc_id = st.selectbox("Active Threats Needing Response", [i.incident_id for i in incidents[::-1]])
    inc = processor.incident_gen.active_incidents[target_inc_id]

    st.markdown(f"#### Recommended Actions for: **{inc.incident_id}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='glass-card'><strong>Manual Containment</strong></div>", unsafe_allow_html=True)
        if st.button(f"🛡️ Isolate Host: {inc.root_cause}"):
            st.warning(f"Isolating {inc.root_cause}... Network interface disabled.")
        if st.button(f"🛡️ Terminate Related Processes"):
            st.warning("Terminating cmd.exe and powershell.exe on affected hosts.")
        if st.button(f"🛡️ Block External IP"):
            st.warning("Force-blocking IP in system firewall.")

    with col2:
        st.markdown("<div class='glass-card'><strong>Automated Workflows (SOAR)</strong></div>", unsafe_allow_html=True)
        st.write("**Scenario:** Network Exfiltration Detected")
        st.write("- [OK] Step 1: Geo-IP Reputation Check")
        st.write("- [OK] Step 2: Destination Port Validation")
        st.write("- [WAIT] Step 3: Trigger Admin Approval for Host Isolation")
        if st.button("🚀 Execute Automated Recovery"):
            st.info("Recovery workflow started. Rotating credentials...")

st.markdown("---")
st.subheader("🛠️ PLAYBOOK REPOSITORY")
st.write("Browse pre-configured MITRE-mapped response strategies.")
st.multiselect("Select Playbooks to review", ["Brute Force Response", "C2 Containment", "Data Loss Prevention", "Ransomware Isolation"], ["Brute Force Response"])
