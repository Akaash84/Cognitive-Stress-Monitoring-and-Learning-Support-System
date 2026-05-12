import os
from typing import Any, Dict, Optional

try:
    from transformers import pipeline
except Exception:
    pipeline = None


class HFClient:
    """Simple Hugging Face client wrapper using transformers pipelines.

    - Attempts to create a text2text-generation pipeline (good for instruction models)
    - Default model: google/flan-t5-base (small/fast). Change via HF_MODEL env var.
    - Runs on CPU by default (device=-1). If you have GPU set device with constructor.
    """

    def __init__(self, model: Optional[str] = None, device: Optional[int] = -1):
        if pipeline is None:
            raise RuntimeError("transformers library not available. Install with: pip install transformers")
        self.model = model or os.getenv("HF_MODEL", "google/flan-t5-base")
        # create pipeline
        self.pipe = pipeline("text2text-generation", model=self.model, device=device)

    def generate(self, prompt: str, max_length: int = 512, do_sample: bool = False, **kwargs) -> Dict[str, Any]:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt is empty or invalid")
        outputs = self.pipe(prompt, max_length=max_length, do_sample=do_sample)
        # pipeline returns list of dicts
        text = None
        if isinstance(outputs, list) and len(outputs) > 0 and isinstance(outputs[0], dict):
            text = outputs[0].get("generated_text") or outputs[0].get("summary_text") or str(outputs[0])
        else:
            text = str(outputs)
        return {"status_code": 200, "raw": outputs, "text": text}
