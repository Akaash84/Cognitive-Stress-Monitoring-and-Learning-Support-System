from groq_client import GroqClient
import os
from pathlib import Path
import re

print("🔥 TEST FILE RUNNING 🔥")

# Use env var GROQ_API_KEY or GEMINI_API_KEY
api_key = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")

# Fallback: read .streamlit/secrets.toml if env var not present
if not api_key:
    try:
        sec_path = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"
        if sec_path.exists():
            text = sec_path.read_text(encoding="utf-8")
            m = re.search(r'^\s*(GROQ_API_KEY|GEMINI_API_KEY)\s*=\s*["\'](.+?)["\']', text, re.MULTILINE)
            if m:
                api_key = m.group(2).strip()
                print("✅ Loaded API key from .streamlit/secrets.toml")
    except Exception as e:
        print(f"⚠️  Failed to read secrets.toml fallback: {e}")

if not api_key:
    raise SystemExit("GROQ_API_KEY or GEMINI_API_KEY not set in environment or .streamlit/secrets.toml")

client = GroqClient(api_key=api_key)

print("STATUS:", end=" ")
try:
    response = client.generate(
        prompt="Say hello in one line",
        model="llama3-8b-8192"
    )
    print("200")
    print("\n✅ FINAL OUTPUT:")
    # Attempt to extract text from common response structures
    out_text = None
    if isinstance(response, dict):
        # chat/completions style
        if "choices" in response and isinstance(response["choices"], list) and response["choices"]:
            first = response["choices"][0]
            if isinstance(first, dict):
                out_text = first.get("message") or first.get("text") or first.get("output")
        # some providers return 'output'
        if out_text is None and "output" in response:
            out_text = response.get("output")
    if out_text is None:
        out_text = str(response)
    print(out_text)
except Exception as e:
    print("ERROR")
    print(e)
