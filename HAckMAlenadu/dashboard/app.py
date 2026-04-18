import streamlit as st
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SENTINEL AI | Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZE STATE & DESIGN ---
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()

# --- REFRESH ---
st_autorefresh(interval=3000, key="global_refresh")

# --- MAIN LANDING (REDIRECT OR OVERVIEW) ---
st.title("🛡️ GLOBAL SECURITY OVERVIEW")
st.caption("WELCOME TO THE SENTINEL AI ENTERPRISE COMMAND CENTER")

# Access real-time state
processor = bridge.get_processor()

# KPI Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("TOTAL TELEMETRY INGESTED", processor.processed_count)
with m2:
    st.metric("ACTIVE INCIDENTS", len(processor.incident_gen.active_incidents))
with m3:
    st.metric("BLOCKED ENTITIES", "0", delta="Live Mode")
with m4:
    status = "SECURE" if len(processor.incident_gen.active_incidents) == 0 else "UNDER ATTACK"
    color = "text-safe" if status == "SECURE" else "text-critical"
    st.markdown(f"### <span class='{color}'>{status}</span>", unsafe_allow_html=True)

st.markdown("---")

# Visual Grid
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<div class='glass-card'><h4>📊 ATTACK TYPE DISTRIBUTION</h4></div>", unsafe_allow_html=True)
    # Placeholder for ECharts/Plotly Pie
    st.info("Ingesting live telemetry to populate distribution...")

with col2:
    st.markdown("<div class='glass-card'><h4>🔥 SYSTEM RISK GAUGE</h4></div>", unsafe_allow_html=True)
    risk_score = min(100, (len(processor.incident_gen.active_incidents) * 35))
    st.progress(risk_score / 100.0)
    st.markdown(f"**Current Risk Index:** {risk_score}%")

st.markdown("---")
st.subheader("📡 GLOBAL ALERT FEED")
incidents = list(processor.incident_gen.active_incidents.values())
if not incidents:
    st.write("No active incidents in the last 15 minutes.")
else:
    for inc in incidents[::-1]:
        severity_class = "text-critical" if inc.severity == "HIGH" else "text-warning"
        st.markdown(f"""
        <div class='glass-card'>
            <span class='{severity_class}'><strong>{inc.severity}</strong></span> | 
            <strong>{inc.incident_id}</strong> | {inc.summary}<br/>
            <small>Entities: {', '.join(inc.entities)}</small>
        </div>
        """, unsafe_allow_html=True)
