import streamlit as st
import asyncio
import threading
from main_enterprise import SentinelXDRController

class XDRStateBridge:
    """
    Singleton Bridge that manages the background XDR Intelligence thread.
    Ensures all 15 dashboard pages access the same real-time security state.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(XDRStateBridge, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.controller = SentinelXDRController()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        print("[BRIDGE] XDR Background Intelligence Thread Started.")

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.controller.start())

    def get_processor(self):
        return self.controller.processor

    def get_manager(self):
        return self.controller.manager

@st.cache_resource
def get_xdr_bridge():
    """Returns the globally shared XDR state bridge."""
    return XDRStateBridge()

def inject_custom_css():
    """Injects the Glassmorphism Design System into the Streamlit page."""
    with open("dashboard/assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_sidebar_header():
    """Unified header for all SOC pages."""
    st.sidebar.image("https://img.icons8.com/nolan/96/shield.png", width=80)
    st.sidebar.title("SENTINEL AI")
    st.sidebar.caption("ENTERPRISE XDR COMMAND CENTER")
    st.sidebar.markdown("---")
