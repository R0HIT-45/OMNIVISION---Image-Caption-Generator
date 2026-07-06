import logging
from typing import Dict, Any
from app.config.settings import get_settings

logger = logging.getLogger("omnivision")
settings = get_settings()

class GroundingService:
    def __init__(self):
        self.threshold = settings.GROUNDING_SIMILARITY_THRESHOLD

    def evaluate_and_ground(self, raw_caption: str, retrieved_entries: list) -> Dict[str, Any]:
        """
        Implements the Confidence Gate logic to prevent AI hallucination.
        """
        logger.info("Evaluating grounding confidence...")
        
        result = {
            "final_caption": raw_caption,
            "grounding_applied": False,
            "top_entity": None,
            "top_fact": None,
            "top_score": 0.0,
            "threshold_used": self.threshold
        }
        
        if not retrieved_entries:
            logger.debug("No retrieval entries provided. Skipping grounding.")
            return result
            
        top_match = retrieved_entries[0]
        score = top_match.get("score", 0.0)
        entity = top_match.get("entity", "Unknown")
        fact = top_match.get("fact", "")
        
        result["top_entity"] = entity
        result["top_fact"] = fact
        result["top_score"] = score
        
        if score >= self.threshold:
            logger.info(f"Confidence HIGH ({score:.3f} >= {self.threshold}). Applying grounding.")
            result["final_caption"] = f"{raw_caption} Context: {fact}"
            result["grounding_applied"] = True
        else:
            logger.info(f"Confidence LOW ({score:.3f} < {self.threshold}). Skipping grounding to avoid hallucination.")
            
        return result
