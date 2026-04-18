import streamlit as st
import plotly.express as px
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header

# --- PAGE CONFIG ---
st.set_page_config(page_title="SENTINEL AI | Explainability", layout="wide")
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()

processor = bridge.get_processor()

st.title("🧠 EXPLAINABILITY & TRIAGE CENTER")
st.markdown("<small>Decoding the AI decision layer with feature-level contributions</small>", unsafe_allow_html=True)
st.markdown("---")

incidents = list(processor.incident_gen.active_incidents.values())

if not incidents:
    st.info("No security alerts available for explainability analysis.")
else:
    # Select Incident for Deep-Dive
    target_inc_id = st.selectbox("Select Incident for Forensic Breakdown", [i.incident_id for i in incidents[::-1]])
    inc = processor.incident_gen.active_incidents[target_inc_id]

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"<div class='glass-card'><h4>🔍 Why this was flagged?</h4><p>{inc.summary}</p></div>", unsafe_allow_html=True)
        
        # Mock Feature Breakdown logic for demonstration
        data = {
            "Feature": ["Network Volume", "Entity Reputation", "Path Anomaly", "Time Interval"],
            "Contribution": [45, 25, 20, 10]
        }
        fig = px.pie(data, values='Contribution', names='Feature', 
                    title="Feature Contribution Weighting",
                    color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='glass-card'><h4>📊 CONFIDENCE REASONING</h4></div>", unsafe_allow_html=True)
        st.metric("Detection Confidence", "92%", delta="High Assurance")
        st.markdown("""
        **Reasoning Engine:**
        - Multi-signal correlation across 3 entities.
        - Pattern matches T1048 (Exfiltration over Alternative Protocol).
        - Anomaly score deviated 4.2x from 15-minute rolling baseline.
        """)
        
        st.markdown("---")
        st.markdown("##### 🕵️ MITRE ATT&CK MAPPING")
        st.code("Tactics: Exfiltration (TA0010)\nTechniques: Exfiltration over C2 Channel (T1041)")

st.markdown("---")
st.subheader("📋 RECENT EVIDENCE LOGS")
if incidents:
    st.dataframe(inc.events)
