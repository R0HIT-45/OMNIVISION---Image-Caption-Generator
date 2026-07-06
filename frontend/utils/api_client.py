import os
import requests
import streamlit as st
from typing import Dict, Any, Optional

# Read API base URL from env or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
TIMEOUT_SECONDS = 120  # AI processing takes time

def process_image(file_bytes: bytes, filename: str, mime_type: str) -> Optional[Dict[str, Any]]:
    """
    Sends the image to the FastAPI backend for full pipeline processing.
    """
    url = f"{API_BASE_URL}/process-image"
    files = {"file": (filename, file_bytes, mime_type)}
    
    try:
        response = requests.post(url, files=files, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            st.session_state.error_message = response.json().get("message", "Validation error.")
            return None
        elif response.status_code == 500:
            st.session_state.error_message = response.json().get("message", "Internal AI Server Error.")
            return None
        else:
            st.session_state.error_message = f"Unexpected error: HTTP {response.status_code}"
            return None
            
    except requests.exceptions.Timeout:
        st.session_state.error_message = "The request timed out. The server might be overloaded or processing took too long."
        return None
    except requests.exceptions.ConnectionError:
        st.session_state.error_message = "Cannot connect to the AI backend. Please ensure the server is running."
        return None
    except Exception as e:
        st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
        return None
