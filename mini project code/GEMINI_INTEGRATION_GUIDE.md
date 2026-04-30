# Gemini AI Stress Analysis Integration

## Overview
This integration adds AI-powered stress analysis to your Cognitive Assessment System. When a user completes a test, the system:

1. **Identifies stress-related questions** - Questions answered during HIGH/Moderate stress periods (via health sensor data)
2. **Fetches question details** - Retrieves the actual questions from `questions.json` using the question IDs
3. **Sends to Gemini API** - Sends the stress-related questions + health metrics to Google's Gemini Pro model
4. **Generates analysis** - Receives structured analysis including:
   - Overall stress assessment with stress score
   - Problem areas causing stress
   - Topic recommendations for improvement
   - Coping strategies
   - Personalized action plan (short/medium/long term)
   - Performance insights

## Setup Instructions

### 1. Install Dependencies
The `google-generativeai` package has been added to `requirements.txt`. Install it:

```bash
pip install -r requirements.txt
```

Or directly:
```bash
pip install google-generativeai
```

### 2. Get Your Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy your API key

### 3. Configure API Key
You have two options:

#### Option A: Environment Variable (Recommended for production)
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key-here"

# Windows CMD
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY="your-api-key-here"
```

#### Option B: Streamlit Secrets (Recommended for Streamlit Cloud)
1. Create `.streamlit/secrets.toml` in your project root:
```toml
GEMINI_API_KEY = "your-api-key-here"
```

2. Or use Streamlit Cloud dashboard:
   - Deploy your app
   - Go to Settings → Secrets
   - Add: `GEMINI_API_KEY = "your-api-key-here"`

### 4. File Changes Made

#### New File: `app/gemini_analysis.py`
Core module with three main functions:

- **`analyze_stress_with_gemini()`** - Main function that:
  - Loads stress-related questions from JSON
  - Calls Gemini API with structured prompt
  - Returns analysis with error handling
  
- **`load_questions_from_json()`** - Searches `questions.json` for questions matching the stress-related QIDs

- **`format_analysis_for_display()`** - Formats Gemini's response into user-friendly markdown

#### Modified: `app/app.py`
1. Added import: `from gemini_analysis import analyze_stress_with_gemini, format_analysis_for_display`
2. Updated `save_submission()` function to:
   - Call `analyze_stress_with_gemini()` after saving submission
   - Store result in `st.session_state.gemini_analysis`
3. Added `gemini_analysis` initialization in `init_state()`
4. Added display section for Gemini analysis in submission results page

#### Modified: `requirements.txt`
- Added `google-generativeai` dependency

## How It Works

### Data Flow

```
User Submits Test
    ↓
fetch_stress_related_questions() → Gets QIDs where stress was HIGH/MODERATE
    ↓
load_questions_from_json() → Fetches full question details from questions.json
    ↓
analyze_stress_with_gemini() → Sends to Gemini API
    ↓
Gemini AI Analysis → Returns structured JSON with recommendations
    ↓
format_analysis_for_display() → Converts to readable markdown
    ↓
Display in UI with expandable raw response
```

### Session State Management

```python
st.session_state.hsqsns  # List of question IDs during stress
st.session_state.health_summary  # Stress metrics (avg_stress, counts, etc.)
st.session_state.gemini_analysis  # AI analysis result
```

## Example Output

When user submits a test with stress-related questions, they'll see:

```
🤖 AI-Powered Stress Analysis

📊 Overall Stress Assessment
- Stress Level: MODERATE
- Stress Score: 6.5/10
- Summary: Your stress increased significantly during numerical reasoning tasks...

🎯 Problem Areas
- NUMERICAL ABILITY (Impact: high)
  - Pattern recognition under time pressure causes elevated stress
- MEMORY TESTS (Impact: medium)
  - Working memory tasks trigger mild cognitive stress

📚 Topics to Focus On
- Numerical Problem Solving (Priority: high)
  - Reason: Most stress spikes occurred here
  - Action: Practice timed numerical reasoning daily for 20 minutes

💪 Coping Strategies
- Time Management: Break problems into 5-minute chunks...
- Deep Breathing: Implement 4-7-8 breathing technique...

🚀 Personalized Action Plan

### Short Term (This Week)
- Take 3 practice tests focusing on numerical reasoning
- Track stress levels during study sessions

### Medium Term (This Month)
- Improve speed in numerical calculations
- Build confidence with progressively harder problems

### Long Term (Next 3 Months)
- Master advanced numerical patterns
- Develop stress-resilient test-taking habits
```

## Error Handling

The system includes comprehensive error handling:

```python
# If API key missing
❌ Error: Gemini API key not found...

# If Gemini API fails
❌ Error: Gemini API error: ...

# If questions.json not found
❌ Error: Failed to load questions.json: ...
```

All errors are gracefully displayed to the user without breaking the app.

## Testing the Integration

### Manual Test

1. Run your Streamlit app:
```bash
streamlit run app/app.py
```

2. Complete a test with health sensor data (ensure stress readings are recorded)

3. At submission, you should see:
   - Stress metrics displayed
   - "🤖 AI-Powered Stress Analysis" section
   - Expandable "View Raw Analysis" section

### Debug Mode

To view the raw Gemini response:
- Click "View Raw Analysis" expander
- Check the JSON response for debugging

## Customization

### Modify Gemini Prompt

Edit the prompt in `gemini_analysis.py` function `analyze_stress_with_gemini()`:

```python
prompt = f"""
Your custom system prompt here...

[Data]
{questions_text}
[End Data]

Provide analysis in this format: {...}
"""
```

### Change Analysis Format

Modify `format_analysis_for_display()` to customize how results are shown.

## API Costs

Google's Gemini API has a **free tier**:
- ⚠️ Limited requests per day
- For production, check [Google AI pricing](https://ai.google.dev/pricing)

## Troubleshooting

### "Gemini API key not found"
- Check environment variable: `echo $GEMINI_API_KEY`
- Check `.streamlit/secrets.toml` exists
- Restart terminal/IDE after setting env variable

### Empty or incomplete analysis
- Check that `questions.json` has questions with matching IDs
- Verify `hsqsns` list is not empty
- Check Gemini API rate limits

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## Files Reference

| File | Purpose |
|------|---------|
| `app/gemini_analysis.py` | Core Gemini integration (NEW) |
| `app/app.py` | Main app with integrated display (MODIFIED) |
| `requirements.txt` | Added google-generativeai (MODIFIED) |
| `data/questions.json` | Question source (used by integration) |
| `.streamlit/secrets.toml` | Your API key (if using secrets) |

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Set your GEMINI_API_KEY environment variable or in secrets.toml
3. ✅ Test by running the app and submitting a test
4. ✅ Customize prompts/output format as needed

## Support

For issues:
1. Check error messages in the app
2. Review the debug output in "View Raw Analysis"
3. Check API key setup
4. Verify questions.json format matches expected structure
