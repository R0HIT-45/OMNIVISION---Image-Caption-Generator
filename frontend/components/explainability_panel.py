import streamlit as st
from typing import Dict, Any

def render_explainability_panel(response_data: Dict[str, Any]):
    """Renders the detailed AI Decision Timeline and Visual Pipeline."""
    
    explainability = response_data.get("explainability", {})
    data = response_data.get("data", {})
    metadata = response_data.get("metadata", {})
    
    if not explainability:
        return
        
    with st.expander("🔍 View AI Decision Timeline (Explainability)", expanded=False):
        st.markdown("### 1. Decision Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Raw Vision Output (BLIP-2)**")
            st.info(data.get("raw_caption", "N/A"))
            
            st.markdown("**Retrieved Knowledge (FAISS)**")
            top_entity = explainability.get("top_retrieved_entity")
            retrieved_fact = explainability.get("retrieved_fact")
            if top_entity:
                st.info(f"**{top_entity}**: {retrieved_fact}")
            else:
                st.warning("No relevant knowledge found in active packs.")
                
        with col2:
            st.markdown("**Confidence Gate Evaluation**")
            score = explainability.get("similarity_score", 0.0)
            threshold = explainability.get("threshold_used", 0.75)
            applied = explainability.get("grounding_applied", False)
            
            st.metric("Cosine Similarity", f"{score:.3f}", delta=f"{score - threshold:.3f} from threshold")
            
            if applied:
                st.success(f"✅ Grounding Applied: Score {score:.3f} >= Threshold {threshold:.2f}")
            else:
                st.error(f"❌ Grounding Rejected (Hallucination Prevented): Score {score:.3f} < Threshold {threshold:.2f}")
                
        st.divider()
        st.markdown("### 2. Execution Pipeline & Performance")
        
        times = metadata.get("processing_times", {})
        models = metadata.get("model_versions", {})
        
        # Draw visual pipeline
        pipeline_stages = [
            ("Vision", times.get("vision_ms", 0.0), models.get("caption", "Unknown")),
            ("Retrieval", times.get("retrieval_ms", 0.0), models.get("embedding", "Unknown")),
            ("Grounding", times.get("grounding_ms", 0.0), "Confidence Gate Algorithm"),
            ("Translation", times.get("translation_ms", 0.0), models.get("translation", "Unknown")),
            ("Audio Synthesis", times.get("audio_ms", 0.0), models.get("tts", "Unknown"))
        ]
        
        for i, (stage, time_ms, model) in enumerate(pipeline_stages):
            status_icon = "✅" if time_ms > 0 else "⏭️"
            st.markdown(f"**{status_icon} {stage}**")
            st.caption(f"Model: `{model}` | Latency: `{time_ms} ms`")
            
            if i < len(pipeline_stages) - 1:
                st.markdown("⬇️")
                
        st.divider()
        st.markdown(f"**Total Pipeline Latency:** `{metadata.get('processing_time_ms', 0.0)} ms`")
        st.markdown(f"**Request ID:** `{response_data.get('request_id', 'Unknown')}`")
