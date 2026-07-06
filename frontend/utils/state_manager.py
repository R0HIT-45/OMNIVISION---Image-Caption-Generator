import streamlit as st

def initialize_state():
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "backend_response" not in st.session_state:
        st.session_state.backend_response = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None

def reset_results_state():
    st.session_state.backend_response = None
    st.session_state.error_message = None
