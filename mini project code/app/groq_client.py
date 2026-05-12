# import os
# import requests
# from typing import Any, Dict, Optional
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry

# class GroqClient:
#     """Minimal, robust Groq HTTP client wrapper.

#     - Requires GROQ_API_KEY (env or constructor).
#     - Uses OpenAI-compatible chat/completions endpoint.
#     - Forces model to 'llama3-8b-8192'.
#     - Uses a requests.Session with retries for transient errors.
#     """

#     def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
#         # Load API key
#         if api_key and isinstance(api_key, str) and api_key.strip():
#             self.api_key = api_key.strip()
#         else:
#             env_key = os.getenv("GROQ_API_KEY")
#             if env_key and isinstance(env_key, str) and env_key.strip():
#                 self.api_key = env_key.strip()

#         if not hasattr(self, 'api_key') or not self.api_key:
#             raise ValueError(
#                 "❌ GROQ API key required.\n"
#                 "Set GROQ_API_KEY in environment OR\n"
#                 "Add to .streamlit/secrets.toml:\n"
#                 "GROQ_API_KEY = \"your_key_here\""
#             )

#         # Base URL must be the OpenAI-compatible Groq endpoint
#         self.base_url = (base_url.strip() if isinstance(base_url, str) and base_url.strip() else "https://api.groq.com/openai/v1")
#         self.timeout = timeout

#         # Prepare session with retries for idempotent safe retries on common transient errors
#         self.session = requests.Session()
#         retries = Retry(total=max_retries, backoff_factor=1, status_forcelist=(429, 502, 503, 504), allowed_methods=("POST",))
#         adapter = HTTPAdapter(max_retries=retries)
#         self.session.mount("https://", adapter)
#         self.session.mount("http://", adapter)

#     def _extract_text_from_response(self, resp_json: Any) -> Optional[str]:
#         # Common OpenAI/Groq chat/completions response shapes
#         try:
#             if isinstance(resp_json, dict):
#                 # choices -> message -> content
#                 choices = resp_json.get("choices")
#                 if isinstance(choices, list) and len(choices) > 0:
#                     first = choices[0]
#                     if isinstance(first, dict):
#                         # Newer style: first['message']['content']
#                         msg = first.get("message")
#                         if isinstance(msg, dict):
#                             content = msg.get("content")
#                             if isinstance(content, str):
#                                 return content
#                         # Older style: first['text']
#                         text = first.get("text")
#                         if isinstance(text, str):
#                             return text
#                 # Some providers return top-level 'output' or 'generated_text'
#                 if "output" in resp_json and isinstance(resp_json["output"], str):
#                     return resp_json["output"]
#                 if "generated_text" in resp_json and isinstance(resp_json["generated_text"], str):
#                     return resp_json["generated_text"]
#             # fallback to None
#             return None
#         except Exception:
#             return None

#     def generate(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, timeout: Optional[int] = None) -> Dict[str, Any]:
#         """Generate text using Groq chat/completions.

#         Returns a dict: {"status_code": int, "raw": <resp_json>, "text": <extracted_text_or_none>}
#         """
#         # Force allowed model
#         model = "llama3-8b-8192"

#         if timeout is None:
#             timeout = self.timeout

#         if not prompt or not isinstance(prompt, str) or not prompt.strip():
#             raise ValueError("Prompt is empty or invalid")

#         url = f"{self.base_url.rstrip('/')}/chat/completions"
#         headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

#         messages = [{"role": "user", "content": prompt}]

#         payload: Dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature}

#         # Debug minimal info
#         print("[groq_client] URL:", url)
#         print("[groq_client] MODEL:", model)
#         print("[groq_client] prompt len:", len(prompt))

#         try:
#             resp = self.session.post(url, json=payload, headers=headers, timeout=timeout)
#             status = resp.status_code
#             try:
#                 resp_text = resp.text
#             except Exception:
#                 resp_text = None

#             if status != 200:
#                 # Provide the server response and status for diagnosis
#                 raise RuntimeError(f"Groq API HTTP error (status={status}). Response: {resp_text}")

#             resp_json = resp.json()
#             extracted = self._extract_text_from_response(resp_json)
#             return {"status_code": status, "raw": resp_json, "text": extracted}

#         except requests.exceptions.RequestException as e:
#             raise RuntimeError(f"Network/HTTP error calling Groq API: {e}") from e

import os
import requests
from typing import Any, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GroqClient:
    """Minimal, robust Groq HTTP client wrapper.

    Requires GROQ_API_KEY (environment or .streamlit/secrets.toml).
    Uses Groq's OpenAI-compatible chat/completions endpoint.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        # Load API key
        if api_key and isinstance(api_key, str) and api_key.strip():
            self.api_key = api_key.strip()
        else:
            env_key = os.getenv("GROQ_API_KEY")
            if env_key and isinstance(env_key, str) and env_key.strip():
                self.api_key = env_key.strip()

        if not hasattr(self, 'api_key') or not self.api_key:
            raise ValueError(
                "❌ GROQ API key required.\n"
                "Set GROQ_API_KEY in environment OR\n"
                "Add to .streamlit/secrets.toml:\n"
                "GROQ_API_KEY = \"your_key_here\""
            )

        # Base URL must be the OpenAI-compatible Groq endpoint
        self.base_url = (base_url.strip() if isinstance(base_url, str) and base_url.strip() else "https://api.groq.com/openai/v1")
        self.timeout = timeout

        # Prepare session with retries for idempotent safe retries on common transient errors
        self.session = requests.Session()
        retries = Retry(total=max_retries, backoff_factor=1, status_forcelist=(429, 502, 503, 504), allowed_methods=("POST",))
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _extract_text_from_response(self, resp_json: Any) -> Optional[str]:
        # Common OpenAI/Groq chat/completions response shapes
        try:
            if isinstance(resp_json, dict):
                # choices -> message -> content
                choices = resp_json.get("choices")
                if isinstance(choices, list) and len(choices) > 0:
                    first = choices[0]
                    if isinstance(first, dict):
                        # Newer style: first['message']['content']
                        msg = first.get("message")
                        if isinstance(msg, dict):
                            content = msg.get("content")
                            if isinstance(content, str):
                                return content
                        # Older style: first['text']
                        text = first.get("text")
                        if isinstance(text, str):
                            return text
                # Some providers return top-level 'output' or 'generated_text'
                if "output" in resp_json and isinstance(resp_json["output"], str):
                    return resp_json["output"]
                if "generated_text" in resp_json and isinstance(resp_json["generated_text"], str):
                    return resp_json["generated_text"]
            # fallback to None
            return None
        except Exception:
            return None

    def generate(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7, timeout: Optional[int] = None) -> Dict[str, Any]:
    
    # ✅ Use working model (NOT deprecated)
        model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        if timeout is None:
            timeout = self.timeout

        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt is empty or invalid")

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        print("[groq_client] MODEL:", model)

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=timeout)

            if resp.status_code != 200:
                raise RuntimeError(f"Groq API HTTP error (status={resp.status_code}). Response: {resp.text}")

            resp_json = resp.json()
            extracted = self._extract_text_from_response(resp_json)

            return {
                "status_code": resp.status_code,
                "raw": resp_json,
                "text": extracted
            }

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network/HTTP error calling Groq API: {e}") from e