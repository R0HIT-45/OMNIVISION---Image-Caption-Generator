import os
import streamlit as st
from typing import Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
# Remove /api/v1 if it exists so we can map to /static/audio
STATIC_BASE_URL = API_BASE_URL.replace("/api/v1", "")

def render_result_display(response_data: Dict[str, Any]):
    """Renders the translated captions and audio players in tabs."""
    st.markdown("### 2. AI Generated Caption")
    
    data = response_data.get("data", {})
    final_caption = data.get("final_caption", "")
    translations = data.get("translations", {})
    audio_urls = data.get("audio_urls", {})
    
    # We always have English. Plus whatever translations came back.
    tabs_labels = ["English"]
    langs_available = ["english"]
    
    for lang in translations.keys():
        tabs_labels.append(lang.capitalize())
        langs_available.append(lang)
        
    tabs = st.tabs(tabs_labels)
    
    for idx, tab in enumerate(tabs):
        with tab:
            lang = langs_available[idx]
            
            # Display Text
            if lang == "english":
                st.markdown(f"> **{final_caption}**")
            else:
                st.markdown(f"> **{translations.get(lang, '')}**")
                
            # Display Audio Player
            audio_path = audio_urls.get(lang)
            if audio_path:
                full_audio_url = f"{STATIC_BASE_URL}{audio_path}"
                st.audio(full_audio_url, format="audio/wav")
            else:
                st.info(f"No audio available for {lang}.")
