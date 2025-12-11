# smart_token_estimator.py
# Minimal, safe token estimator with optional tiktoken support.

from typing import Optional

try:
    import tiktoken  # optional, better accuracy
except Exception:
    tiktoken = None


class SmartTokenEstimator:
    """
    Estimate token counts for a given model. Falls back to a simple word-based
    heuristic if tiktoken or the model encoding aren't available.
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.enc = None

        if tiktoken:
            try:
                self.enc = tiktoken.encoding_for_model(model)
            except Exception:
                try:
                    # Common fallback for OpenAI chat models
                    self.enc = tiktoken.get_encoding("cl100k_base")
                except Exception:
                    self.enc = None

    def estimate(self, text: Optional[str]) -> int:
        if not text:
            return 0
        if self.enc:  # accurate path
            try:
                return len(self.enc.encode(text))
            except Exception:
                pass
        # fallback heuristic: ~1 token ≈ 0.75 words (conservative)
        return max(1, int(len(text.split()) / 0.75))
