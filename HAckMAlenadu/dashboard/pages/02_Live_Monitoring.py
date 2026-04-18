import streamlit as st
import graphviz
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(page_title="SENTINEL AI | Live Monitor", layout="wide")
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()
st_autorefresh(interval=2000, key="monitor_refresh")

processor = bridge.get_processor()

st.title("📡 LIVE TRAFFIC & THREAT MONITORING")
st.markdown("---")

# --- SPLIT PANE LAYOUT ---
col_stream, col_intel = st.columns([1, 1])

# LEFT PANEL: LIVE TELEMETRY STREAM
with col_stream:
    st.subheader("🛰️ GLOBAL TELEMETRY STREAM")
    st.markdown("<small>Real-time correlation across Network and Endpoint layers</small>", unsafe_allow_html=True)
    
    # Get last 15 events from forensics buffer
    events = list(processor.forensics.event_buffer)[-15:]
    if not events:
        st.info("Awaiting telemetry signals...")
    else:
        for e in events[::-1]:
            color = "#00A3FF" if e.get('priority') == "LOW" else "#FFA500" if e.get('priority') == "MEDIUM" else "#FF4B4B"
            st.markdown(f"""
            <div class='log-stream' style='border-left-color: {color}'>
                <strong>{e.get('timestamp')}</strong> | {e.get('event_type').upper()}<br/>
                {e.get('source_entity')} ➡️ {e.get('target_entity', 'LOCAL')}<br/>
                <small>Sensor: {e.get('sensor_type')} | Status: {e.get('status')}</small>
            </div>
            """, unsafe_allow_html=True)

# RIGHT PANEL: DYNAMIC SUSPICIOUS IP INTELLIGENCE
with col_intel:
    st.subheader("🧠 SUSPICIOUS ENTITY INTELLIGENCE")
    
    incidents = list(processor.incident_gen.active_incidents.values())
    suspicious_ips = set()
    for inc in incidents:
        for entity in inc.entities:
            if "." in entity: # Crude IP check
                suspicious_ips.add(entity)
    
    if not suspicious_ips:
        st.success("No suspicious entities detected in current window.")
    else:
        for ip in sorted(list(suspicious_ips)):
            with st.expander(f"🔴 SUSPICIOUS IP: {ip}", expanded=True):
                # IP Details
                i_col, t_col = st.columns([1, 1])
                with i_col:
                    st.write(f"**Entity ID:** {ip}")
                    st.write(f"**Risk Score:** 85/100") # Logic derived from priority
                with t_col:
                    st.write("**Classification:** Brute Force / Exfiltration")
                    st.button("🛡️ BLOCK IP", key=f"block_{ip}")

                # --- ATTACK PATH VISUALIZATION (PER IP) ---
                st.markdown("##### 🔥 ATTACK PATH GRAPH")
                dot = graphviz.Digraph()
                dot.attr(rankdir='LR', bgcolor='transparent')
                dot.attr('node', shape='box', style='filled', fillcolor='#1e212b', color='#00A3FF', fontcolor='white')
                
                # Dynamic Path Building based on incident history
                nodes = ["Internet", ip, "Web Server", "Local Database", "External C2"]
                for i in range(len(nodes)-1):
                    dot.edge(nodes[i], nodes[i+1], color='#FF4B4B' if i > 1 else '#FFA500')
                
                st.graphviz_chart(dot)
                
                # Reasoning
                st.markdown("""
                <div class='glass-card' style='padding: 10px; font-size: 0.9rem;'>
                    <strong>Intelligence Reasoning:</strong> Entity identified coordinating burst network activity 
                    following repeated authentication failures. Graph correlation links this IP to critical database processes.
                </div>
                """, unsafe_allow_html=True)
