# Deprecated diagnostic tool
# This project migrated from Google Gemini to Groq. The old Gemini diagnostic
# helper has been removed. If you need to verify your AI API key or access,
# use `app/groq_client.py` and set the environment variable `GROQ_API_KEY`.
#
# Quick checks you can run in PowerShell (temporary for session):
# $env:GROQ_API_KEY = 'your-key-here'
# python -c "import os; print('GROQ key found:', bool(os.getenv('GROQ_API_KEY')) )"
#
# You can safely delete this file if you no longer need Gemini-specific checks.
