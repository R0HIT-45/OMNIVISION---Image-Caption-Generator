import streamlit as st
from utils.state_manager import reset_results_state

def render_upload_component():
    """Renders the file uploader and handles state changes on new upload."""
    st.markdown("### 1. Upload Image")
    uploaded_file = st.file_uploader(
        "Drag and drop file here", 
        type=["png", "jpg", "jpeg"],
        help="Maximum file size: 10MB",
        disabled=st.session_state.is_processing
    )
    
    if uploaded_file is not None:
        # If a new file is uploaded, reset the previous results
        if st.session_state.uploaded_file != uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            reset_results_state()
            
        st.image(uploaded_file, caption="Image Preview", use_container_width=True)
    else:
        # If user clears the upload, reset state
        st.session_state.uploaded_file = None
        reset_results_state()
