import streamlit as st
import asyncio
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header
from core.common.schema import create_ues_event

# --- PAGE CONFIG ---
st.set_page_config(page_title="SENTINEL AI | Simulator", layout="wide")
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()

processor = bridge.get_processor()

st.title("🚨 ATTACK SIMULATION CONTROL PANEL")
st.markdown("<small>Inject mission-critical attack scenarios into the live pipeline</small>", unsafe_allow_html=True)
st.markdown("---")

async def inject_event(event):
    await bridge.controller.inbox.push(event)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='glass-card'><h4>🔑 Brute Force</h4></div>", unsafe_allow_html=True)
    st.write("Simulates a high-frequency credential stuffing attempt.")
    if st.button("🚀 Trigger Brute Force"):
        for i in range(10):
            e = create_ues_event("sim_engine", "login_attempt", f"192.168.1.5", "admin-portal", priority="LOW", status="failed")
            asyncio.run(inject_event(e))
        success = create_ues_event("sim_engine", "login_attempt", f"192.168.1.5", "admin-portal", priority="HIGH", status="success")
        asyncio.run(inject_event(success))
        st.success("Scenario Injected: Brute Force Success detected.")

with col2:
    st.markdown("<div class='glass-card'><h4>📡 C2 Beaconing</h4></div>", unsafe_allow_html=True)
    st.write("Simulates command & control heartbeat activity.")
    if st.button("🚀 Trigger C2 Beacon"):
        e = create_ues_event("sim_engine", "network_connect", "workstation-01", "13.37.13.37", priority="MEDIUM", port=4444)
        asyncio.run(inject_event(e))
        st.success("Scenario Injected: C2 Heartbeat registered.")

with col3:
    st.markdown("<div class='glass-card'><h4>💾 Data Exfiltration</h4></div>", unsafe_allow_html=True)
    st.write("Simulates a high-volume outbound data transfer.")
    if st.button("🚀 Trigger Data Exfil"):
        e = create_ues_event("sim_engine", "network_connect", "file-server-01", "external-storage.com", priority="HIGH", bytes_out=6000000)
        asyncio.run(inject_event(e))
        st.success("Scenario Injected: 6MB Data Transfer detected.")

st.markdown("---")
st.subheader("🛠️ SIMULATION HEALTH")
st.progress(processor.processed_count / 1000.0 if processor.processed_count < 1000 else 1.0)
st.write(f"Total Simulated Events Processed: {processor.processed_count}")
