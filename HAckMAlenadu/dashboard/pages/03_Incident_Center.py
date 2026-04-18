import streamlit as st
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(page_title="SENTINEL AI | Incidents", layout="wide")
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()
st_autorefresh(interval=3000, key="incident_refresh")

processor = bridge.get_processor()

st.title("🟣 INCIDENT MANAGEMENT CENTER")
st.markdown("<small>Lifecycle tracking for correlated security incidents</small>", unsafe_allow_html=True)
st.markdown("---")

incidents = list(processor.incident_gen.active_incidents.values())

if not incidents:
    st.info("No active incidents. The system is operating within normal parameters.")
else:
    # Incident Statistics
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("OPEN INCIDENTS", len([i for i in incidents if i.status == "OPEN"]))
    with c2: st.metric("CRITICAL SEVERITY", len([i for i in incidents if i.severity == "HIGH"]))
    with c3: st.metric("MEAN TIME TO DETECT", "1.2s")

    st.markdown("---")

    for inc in incidents[::-1]:
        severity_color = "#FF4B4B" if inc.severity == "HIGH" else "#FFA500"
        with st.container():
            st.markdown(f"""
            <div class='glass-card' style='border-left: 5px solid {severity_color}'>
                <h4 style='margin:0'>{inc.incident_id} | {inc.summary}</h4>
                <p style='color: #8B949E; font-size: 0.9rem;'>
                    Severity: <span style='color: {severity_color};'>{inc.severity}</span> | 
                    Status: {inc.status} | 
                    Created: {inc.created_at}
                </p>
                <p><strong>Affected Entities:</strong> {', '.join(inc.entities)}</p>
                <p><strong>Root Cause:</strong> {getattr(inc, 'root_cause', 'Determining...')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Row
            a1, a2, a3, a4 = st.columns(4)
            with a1: st.button("👁️ Visual Correlation", key=f"vis_{inc.incident_id}")
            with a2: st.button("🎬 Story Mode (Replay)", key=f"story_{inc.incident_id}")
            with a3: st.button("🛡️ Run Playbook", key=f"play_{inc.incident_id}")
            with a4: st.button("✅ Mark Resolved", key=f"res_{inc.incident_id}")
            st.markdown("---")
