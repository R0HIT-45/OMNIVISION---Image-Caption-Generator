import logging
import os
from typing import Dict

from backend.app.config.settings import get_settings
from backend.app.exceptions.handlers import TTSException
from backend.app.managers.model_manager import get_model_manager

logger = logging.getLogger("omnivision")
settings = get_settings()


class TTSService:
    def __init__(self):
        self.model_manager = get_model_manager()
        self.audio_dir = settings.AUDIO_DIR
        # Map our internal language names to XTTS language codes
        self.lang_codes = {
            "english": "en",
            "hindi": "hi",
            "telugu": "te",  # Note: check if XTTS v2 officially supports te. If not, might fallback or skip.
        }

        # XTTS requires a speaker reference wav file to clone the voice.
        # For simplicity, we assume there's a default.wav in the audio dir,
        # or we might need to handle it differently.
        self.speaker_wav = os.path.join(self.audio_dir, "default_speaker.wav")
        if not os.path.exists(self.speaker_wav):
            # In a real scenario, you'd create or download a small clean 3-second wav here.
            logger.warning(f"Speaker reference {self.speaker_wav} missing. TTS might fail.")

    def warm_up(self):
        logger.info(
            "TTS warm-up skipped (lazy-load to preserve VRAM for caption/embedding/translation)"
        )

    def shutdown(self):
        self.model_manager.unload_model("tts")

    def generate(self, texts: Dict[str, str], request_id: str) -> Dict[str, str]:
        logger.info("Generating audio narrations...")
        audio_paths = {}

        if not os.path.exists(self.speaker_wav):
            logger.error("Skipping TTS because speaker reference is missing.")
            return audio_paths

        try:
            tts_bundle = self.model_manager.get_model("tts")
            model = tts_bundle["model"]

            for lang, text in texts.items():
                if lang not in self.lang_codes:
                    continue

                xtts_code = self.lang_codes[lang]
                file_name = f"{request_id}_{lang}.wav"
                out_path = os.path.join(self.audio_dir, file_name)

                logger.debug(f"Generating TTS for {lang} -> {out_path}")

                # TTS logic
                model.tts_to_file(
                    text=text, speaker_wav=self.speaker_wav, language=xtts_code, file_path=out_path
                )

                # Store the relative path for the frontend
                audio_paths[lang] = f"/static/audio/{file_name}"

            logger.info("TTS generation complete.")
            return audio_paths

        except Exception as e:
            logger.error(f"TTS failed: {str(e)}")
            raise TTSException(f"TTS failed: {str(e)}")
