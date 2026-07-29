import logging
from typing import Any, Dict

from backend.app.config.settings import get_settings

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
            "threshold_used": self.threshold,
            "confidenceLabel": None,
            "matchedEntity": None,
            "reason": None,
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

        if score >= 0.8:
            logger.info(f"Confidence HIGH ({score:.3f}). Applying grounding.")
            result["confidenceLabel"] = "High"
            result["reason"] = f"Strong contextual match found ({score:.2f})."
            result["final_caption"] = f"{raw_caption} Context: {fact}"
            result["grounding_applied"] = True
        elif score >= 0.6:
            logger.info(f"Confidence MEDIUM ({score:.3f}). Proceeding with caution.")
            result["confidenceLabel"] = "Medium"
            result["reason"] = f"Moderate match found ({score:.2f})."
            result["final_caption"] = f"{raw_caption} Context: {fact}"
            result["grounding_applied"] = True if score >= self.threshold else False
        elif score >= 0.4:
            logger.info(f"Confidence LOW ({score:.3f}). Skipping grounding.")
            result["confidenceLabel"] = "Low"
            result["reason"] = f"Weak match found ({score:.2f}). Context may be unreliable."
            result["grounding_applied"] = False
        else:
            logger.info(
                f"Confidence REJECT ({score:.3f}). Skipping grounding to avoid hallucination."
            )
            result["confidenceLabel"] = "Reject"
            result["reason"] = f"No reliable context found ({score:.2f}). Using raw caption."
            result["grounding_applied"] = False

        result["matchedEntity"] = entity
        return result
