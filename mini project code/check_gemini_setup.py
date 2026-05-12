# #!/usr/bin/env python3
# """
# Quick setup checklist and test script for Gemini Integration
# Run this to verify everything is set up correctly
# """

# import os
# import sys
# import json
# from pathlib import Path

# def check_api_key():
#     """Check if Gemini API key is available"""
#     api_key = os.getenv("GEMINI_API_KEY")
#     if api_key:
#         return True, f"✅ API Key found (env var): {api_key[:10]}..."
    
#     secrets_path = Path(".streamlit/secrets.toml")
#     if secrets_path.exists():
#         try:
#             import tomllib if sys.version_info >= (3, 11) else None
#             if tomllib is None:
#                 import toml as tomllib
#             with open(secrets_path, "r") as f:
#                 secrets = tomllib.loads(f.read()) if hasattr(tomllib, 'loads') else tomllib.load(f)
#                 if "GEMINI_API_KEY" in secrets:
#                     return True, f"✅ API Key found (secrets.toml)"
#         except Exception as e:
#             return False, f"❌ Error reading secrets.toml: {e}"
    
#     return False, "❌ Gemini API key not found. Set GEMINI_API_KEY env var or create .streamlit/secrets.toml"

# def check_requirements():
#     """Check if all dependencies are installed"""
#     required = ["streamlit", "google.generativeai", "supabase", "pandas"]
#     missing = []
    
#     for pkg in required:
#         try:
#             __import__(pkg.replace("google.generativeai", "google"))
#         except ImportError:
#             missing.append(pkg)
    
#     if not missing:
#         return True, "✅ All dependencies installed"
#     return False, f"❌ Missing packages: {', '.join(missing)}\nRun: pip install -r requirements.txt"

# def check_files():
#     """Check if all required files exist"""
#     files = [
#         "app/gemini_analysis.py",
#         "app/app.py",
#         "data/questions.json",
#         "requirements.txt"
#     ]
    
#     missing = []
#     for file in files:
#         if not Path(file).exists():
#             missing.append(file)
    
#     if not missing:
#         return True, "✅ All required files found"
#     return False, f"❌ Missing files: {', '.join(missing)}"

# def check_questions_json():
#     """Check if questions.json has expected structure"""
#     try:
#         with open("data/questions.json", "r") as f:
#             questions = json.load(f)
        
#         if isinstance(questions, dict) and len(questions) > 0:
#             # Count total questions
#             total = 0
#             for category, diffs in questions.items():
#                 if isinstance(diffs, dict):
#                     for diff, qs in diffs.items():
#                         if isinstance(qs, list):
#                             total += len(qs)
            
#             if total > 0:
#                 return True, f"✅ Questions.json valid ({len(questions)} categories, {total} questions)"
#             return False, "❌ questions.json is empty"
#         return False, "❌ questions.json has unexpected structure"
#     except json.JSONDecodeError as e:
#         return False, f"❌ questions.json is invalid JSON: {e}"
#     except FileNotFoundError:
#         return False, "❌ questions.json not found"

# def main():
#     print("\n" + "="*60)
#     print("🔍 Gemini Integration Setup Checker")
#     print("="*60 + "\n")
    
#     checks = [
#         ("Dependencies", check_requirements),
#         ("Required Files", check_files),
#         ("API Key", check_api_key),
#         ("Questions.json", check_questions_json),
#     ]
    
#     results = []
#     for name, check_func in checks:
#         success, message = check_func()
#         results.append((success, name, message))
#         print(f"{name}: {message}")
    
#     print("\n" + "="*60)
#     all_passed = all(r[0] for r in results)
    
#     if all_passed:
#         print("✅ All checks passed! You're ready to use Gemini integration.")
#         print("\nNext steps:")
#         print("1. Run: streamlit run app/app.py")
#         print("2. Complete a test with health sensor data")
#         print("3. Check the submission results for 'AI-Powered Stress Analysis'")
#     else:
#         print("❌ Some checks failed. Fix the issues above and try again.")
#         print("\nFor help, see: GEMINI_INTEGRATION_GUIDE.md")
    
#     print("="*60 + "\n")
#     return 0 if all_passed else 1

# if __name__ == "__main__":
#     sys.exit(main())

# # Deprecated: Gemini setup helper removed
# # This project has migrated from Google Gemini to Groq.
# # The old helper utilities for verifying Gemini keys have been removed.
# # If you need to check your Groq setup, use app/groq_client.py and set GROQ_API_KEY.
# # You can safely delete this file.
