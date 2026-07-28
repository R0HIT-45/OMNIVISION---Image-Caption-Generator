import logging
from typing import Dict

import torch

from backend.app.exceptions.handlers import TranslationException
from backend.app.managers.model_manager import get_model_manager

logger = logging.getLogger("omnivision")


class TranslationService:
    def __init__(self):
        self.model_manager = get_model_manager()
        # NLLB specific language codes
        self.lang_codes = {"hindi": "hin_Deva", "telugu": "tel_Telu"}

    def warm_up(self):
        self.model_manager.get_model("translation")

    def translate(self, text: str) -> Dict[str, str]:
        logger.info("Generating translations...")
        results = {}

        try:
            trans_bundle = self.model_manager.get_model("translation")
            tokenizer = trans_bundle["tokenizer"]
            model = trans_bundle["model"]
            device = self.model_manager.device

            for lang, code in self.lang_codes.items():
                logger.debug(f"Translating to {lang}...")

                # NLLB specific prefixing
                tokenizer.src_lang = "eng_Latn"
                inputs = tokenizer(text, return_tensors="pt").to(device)

                generated_tokens = model.generate(
                    **inputs,
                    forced_bos_token_id=(
                        tokenizer.lang_code_to_id[code]
                        if hasattr(tokenizer, "lang_code_to_id")
                        else None
                    ),
                    max_length=256,
                )

                translated_text = tokenizer.batch_decode(
                    generated_tokens, skip_special_tokens=True
                )[0]
                results[lang] = translated_text

                del inputs
                del generated_tokens

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Translations complete.")
            return results

        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            # Translation is non-critical, we don't want to crash the whole request
            raise TranslationException(f"Translation failed: {str(e)}")
