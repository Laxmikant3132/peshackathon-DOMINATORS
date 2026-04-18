import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from dashboard.state_manager import get_xdr_bridge, inject_custom_css, render_sidebar_header

# --- PAGE CONFIG ---
st.set_page_config(page_title="SENTINEL AI | Graph Explorer", layout="wide")
bridge = get_xdr_bridge()
inject_custom_css()
render_sidebar_header()

processor = bridge.get_processor()

st.title("🟡 GLOBAL INCIDENT GRAPH VIEW")
st.markdown("<small>System-wide entity relationship mapping (XDR Core View)</small>", unsafe_allow_html=True)
st.markdown("---")

# Interactive Graph Creation
st.subheader("🕸️ ENTITY RELATIONSHIP EXPLORER")

# 1. Build PyVis Graph from processor.graph
net = Network(height="600px", width="100%", bgcolor="#0a0b10", font_color="white")
net.barnes_hut()

# Populate from live graph
for node, data in processor.graph.graph.nodes(data=True):
    color = "#00A3FF" # Default Blue
    if data.get('type') == 'entity':
        # Check if node is part of an active incident
        for inc in processor.incident_gen.active_incidents.values():
            if node in inc.entities:
                color = "#FF4B4B" # Red for threat-connected nodes
    
    net.add_node(node, label=node, color=color, size=25 if color == "#FF4B4B" else 15)

for u, v, data in processor.graph.graph.edges(data=True):
    net.add_edge(u, v, title=data.get('type'), color="rgba(255,255,255,0.2)")

# 2. Render
try:
    net.save_graph("graph.html")
    with open("graph.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=650)
except Exception as e:
    st.error(f"Graph rendering issue: {e}")
    st.info("Ensure PyVis is correctly handling the backend graph stream.")

st.markdown("---")
st.markdown("""
<div class='glass-card'>
    <strong>Legend:</strong><br/>
    <span style='color: #FF4B4B;'>● Red Nodes</span>: Entities involved in active incidents.<br/>
    <span style='color: #00A3FF;'>● Blue Nodes</span>: Monitored entities (Healthy).<br/>
    <small>Hover over edges to see connection types (Network/Process/Auth).</small>
</div>
""", unsafe_allow_html=True)
