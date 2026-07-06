import os
import streamlit as st
from utils.state_manager import initialize_state
from utils.api_client import process_image
from components.upload_component import render_upload_component
from components.result_display import render_result_display
from components.explainability_panel import render_explainability_panel

# Configure Streamlit Page
st.set_page_config(
    page_title="OmniVision",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load Custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()
initialize_state()

# App Header
st.title("👁️ OmniVision")
st.subheader("AI-Powered Image Caption Generator with Context-Aware Visual Grounding")
st.divider()

# Layout layout
col1, col2 = st.columns([1, 1.2])

with col1:
    render_upload_component()
    
    # Generate Button
    if st.session_state.uploaded_file is not None:
        if st.button("Generate Caption & Narration", type="primary", use_container_width=True, disabled=st.session_state.is_processing):
            st.session_state.is_processing = True
            st.session_state.error_message = None
            st.session_state.backend_response = None
            st.rerun()

# Processing Logic
if st.session_state.is_processing and st.session_state.uploaded_file is not None:
    with col2:
        with st.spinner("Analyzing image and retrieving knowledge... (This may take up to 20 seconds)"):
            file = st.session_state.uploaded_file
            # Call API
            response = process_image(file.getvalue(), file.name, file.type)
            
            if response:
                st.session_state.backend_response = response
            
            st.session_state.is_processing = False
            st.rerun()

with col2:
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
    elif st.session_state.backend_response:
        render_result_display(st.session_state.backend_response)

# Explainability Panel (Full width at bottom)
if st.session_state.backend_response:
    st.divider()
    render_explainability_panel(st.session_state.backend_response)
