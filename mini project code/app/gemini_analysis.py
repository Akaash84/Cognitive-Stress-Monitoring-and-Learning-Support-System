"""
Gemini-based stress analysis for cognitive assessment results.
Fetches stress-related questions and provides personalized recommendations.
"""

import json
import os
from typing import Any, Dict, List, Optional
# import google.generativeai as genai
from google import genai


def _get_gemini_api_key() -> Optional[str]:
    """
    Retrieve Gemini API key from environment or Streamlit secrets.
    Tries multiple methods to ensure compatibility with different setups.
    """
    # Method 1: Try environment variable first
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key and api_key.strip():
        return api_key.strip()

    # Method 2: Try Streamlit secrets
    try:
        import streamlit as st
        
        # Try direct access
        if hasattr(st, 'secrets') and st.secrets:
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key and isinstance(api_key, str) and api_key.strip():
                return api_key.strip()
            
            # Try with different key variations
            for key_name in ["gemini_api_key", "GEMINI_KEY", "gemini_key", "api_key","GEMINI_API_KEY"]:
                api_key = st.secrets.get(key_name)
                if api_key and isinstance(api_key, str) and api_key.strip():
                    return api_key.strip()
    except AttributeError:
        # st.secrets not available (might be outside Streamlit context)
        pass
    except Exception as e:
        # Silently fail for other errors
        pass
    
    return None


def load_questions_from_json(qids: List[str]) -> Dict[str, Any]:
    """
    Load questions from questions.json based on provided QIDs.
    
    Args:
        qids: List of question IDs (e.g., ["NA-1", "NA-2"])
    
    Returns:
        Dictionary with matched questions grouped by type/domain
    """
    try:
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "questions.json")
        
        with open(json_path, "r", encoding="utf-8-sig") as f:
            all_questions = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load questions.json: {str(e)}", "matched_questions": []}

    matched_questions = []
    qid_set = set(q.strip().upper() for q in qids if q)

    # Iterate through all categories and difficulty levels
    for category, difficulty_dict in all_questions.items():
        if isinstance(difficulty_dict, dict):
            for difficulty, questions_list in difficulty_dict.items():
                if isinstance(questions_list, list):
                    for question in questions_list:
                        if isinstance(question, dict):
                            qid = str(question.get("id", "")).strip().upper()
                            if qid in qid_set:
                                matched_questions.append({
                                    "id": qid,
                                    "category": category,
                                    "difficulty": difficulty,
                                    "type": question.get("type", ""),
                                    "question": question.get("question", ""),
                                    "answer": question.get("answer", ""),
                                    "options": question.get("options", {}),
                                    "input_type": question.get("input_type", "mcq"),
                                })

    return {
        "matched_questions": matched_questions,
        "total_matched": len(matched_questions),
        "total_requested": len(qids),
    }


def analyze_stress_with_gemini(
    hsqsns: List[str],
    health_summary: Dict[str, Any],
    test_score: float,
    max_score: float,
    time_taken_seconds: int,
    test_type: str = "foundation",
) -> Dict[str, Any]:
    """
    Send stress-related questions and health metrics to Gemini for AI analysis.
    
    Args:
        hsqsns: List of question IDs related to high/moderate stress
        health_summary: Dict with avg_stress, moderate_high_count, row_count
        test_score: User's score
        max_score: Maximum possible score
        time_taken_seconds: Time spent on test
        test_type: Type of test (foundation/advanced)
    
    Returns:
        Dict with overall_stress_analysis, topic_recommendations, suggestions
    """
    api_key = _get_gemini_api_key()
    print(api_key)
    if not api_key:
        return {
            "error": "Gemini API key not found. Set GEMINI_API_KEY in environment or secrets.",
            "status": "error"
        }

    # try:
    #     genai.configure(api_key=api_key)
    # except Exception as e:
    #     return {
    #         "error": f"Failed to configure Gemini API: {str(e)}",
    #         "status": "error"
    #     }

    # Load the actual questions from JSON
    questions_data = load_questions_from_json(hsqsns)
    
    if "error" in questions_data:
        return {
            "error": questions_data["error"],
            "status": "error"
        }

    # Calculate score percentage
    score_percentage = (test_score / max_score * 100) if max_score > 0 else 0

    # Format questions for Gemini
    questions_text = "\n\n".join([
        f"Q{i+1} ({q['category']} - {q['difficulty']}):\n"
        f"Question: {q['question']}\n"
        f"Type: {q['type']}\n"
        f"Answer: {q['answer']}"
        for i, q in enumerate(questions_data.get("matched_questions", [])[:10])  # Limit to 10 for context
    ])

    if not questions_text:
        questions_text = "No specific questions matched. User experienced stress during test without clear question association."

    # Build comprehensive prompt for Gemini
    prompt = f"""
You are an expert cognitive assessment analyst specializing in stress management and personalized learning recommendations.

## User's Test Performance Data:
- Test Type: {test_type}
- Score: {test_score:.2f}/{max_score:.2f} ({score_percentage:.1f}%)
- Time Taken: {time_taken_seconds // 60} minutes {time_taken_seconds % 60} seconds
- Average Stress Level (0-10): {health_summary.get('avg_stress', 'N/A')}
- High/Moderate Stress Instances: {health_summary.get('moderate_high_count', 0)}
- Total Health Readings: {health_summary.get('row_count', 0)}

## Questions Where User Experienced High/Moderate Stress:
{questions_text}

Based on the above data, provide a comprehensive analysis in the following JSON format:

{{
    "overall_stress_analysis": {{
        "stress_level": "low|moderate|high",
        "stress_score": <0-10>,
        "summary": "2-3 sentence summary of overall stress pattern"
    }},
    "problem_areas": [
        {{
            "category": "category name",
            "stress_factor": "why this area causes stress",
            "impact": "high|medium|low"
        }}
    ],
    "topic_recommendations": [
        {{
            "topic": "specific topic",
            "priority": "high|medium|low",
            "reason": "why focus on this",
            "suggested_action": "specific practice recommendation"
        }}
    ],
    "coping_strategies": [
        {{
            "strategy": "strategy name",
            "description": "how to implement",
            "expected_benefit": "what improvement to expect"
        }}
    ],
    "personalized_suggestions": {{
        "short_term": ["action 1", "action 2", "action 3"],
        "medium_term": ["focus 1", "focus 2"],
        "long_term": ["goal 1", "goal 2"]
    }},
    "performance_insight": "1-2 sentence insight about performance vs stress"
}}

Important:
- Be specific and actionable
- Consider the stress levels recorded during the test
- Provide encouraging but honest feedback
- Focus on improvement areas
"""

    try:
        # model = genai.GenerativeModel("gemini-2.5-flash")
        client = genai.Client(api_key=api_key)
        print("RUNNING NEW GEMINI CODE")
        
        response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=prompt
        )
        
        response_text = response.text
        # model = genai.GenerativeModel("gemini-1.5-flash")
        # response = model.generate_content(prompt)
        
        if not response.text:
            return {
                "error": "Gemini returned empty response",
                "status": "error"
            }

        # Try to parse JSON from response
        response_text = response.text
        
        # Look for JSON block in response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            try:
                analysis = json.loads(json_match.group(0))
                return {
                    "status": "success",
                    "analysis": analysis,
                    "raw_response": response_text,
                    "api_key": api_key,
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                return {
                    "status": "partial",
                    "raw_analysis": response_text,
                    "note": "Could not parse structured JSON, returning raw analysis"
                }
        else:
            return {
                "status": "partial",
                "raw_analysis": response_text,
                "note": "No JSON found in response, returning raw analysis"
            }

    except Exception as e:
        return {
            "error": f"Gemini API error: {str(e)}",
            "status": "error"
        }


def format_analysis_for_display(analysis_response: Dict[str, Any]) -> str:
    """
    Format Gemini analysis response for user-friendly display in Streamlit.
    
    Args:
        analysis_response: Response from analyze_stress_with_gemini
    
    Returns:
        Formatted markdown string
    """
    if analysis_response.get("status") == "error":
        return f"❌ Error: {analysis_response.get('error', 'Unknown error')}"

    if analysis_response.get("status") == "partial":
        return f"📋 Analysis:\n\n{analysis_response.get('raw_analysis', 'No analysis available')}"

    analysis = analysis_response.get("analysis", {})
    
    markdown_output = "# 📊 Stress Analysis Report\n\n"

    # Overall Stress Analysis
    stress_info = analysis.get("overall_stress_analysis", {})
    stress_level = stress_info.get("stress_level", "unknown").upper()
    stress_score = stress_info.get("stress_score", "N/A")
    markdown_output += f"""## Overall Stress Assessment
- **Stress Level**: {stress_level}
- **Stress Score**: {stress_score}/10
- **Summary**: {stress_info.get('summary', 'N/A')}

"""

    # Problem Areas
    problem_areas = analysis.get("problem_areas", [])
    if problem_areas:
        markdown_output += "## 🎯 Problem Areas\n"
        for area in problem_areas:
            markdown_output += f"- **{area.get('category')}** (Impact: {area.get('impact')})\n"
            markdown_output += f"  - {area.get('stress_factor', 'N/A')}\n"
        markdown_output += "\n"

    # Topic Recommendations
    topics = analysis.get("topic_recommendations", [])
    if topics:
        markdown_output += "## 📚 Topics to Focus On\n"
        for topic in topics:
            markdown_output += f"- **{topic.get('topic')}** (Priority: {topic.get('priority')})\n"
            markdown_output += f"  - *Reason*: {topic.get('reason', 'N/A')}\n"
            markdown_output += f"  - *Action*: {topic.get('suggested_action', 'N/A')}\n"
        markdown_output += "\n"

    # Coping Strategies
    strategies = analysis.get("coping_strategies", [])
    if strategies:
        markdown_output += "## 💪 Coping Strategies\n"
        for strategy in strategies:
            markdown_output += f"- **{strategy.get('strategy')}**: {strategy.get('description', 'N/A')}\n"
            markdown_output += f"  - Expected benefit: {strategy.get('expected_benefit', 'N/A')}\n"
        markdown_output += "\n"

    # Personalized Suggestions
    suggestions = analysis.get("personalized_suggestions", {})
    if suggestions:
        markdown_output += "## 🚀 Personalized Action Plan\n"
        
        short_term = suggestions.get("short_term", [])
        if short_term:
            markdown_output += "### Short Term (This Week)\n"
            for item in short_term:
                markdown_output += f"- {item}\n"
        
        medium_term = suggestions.get("medium_term", [])
        if medium_term:
            markdown_output += "### Medium Term (This Month)\n"
            for item in medium_term:
                markdown_output += f"- {item}\n"
        
        long_term = suggestions.get("long_term", [])
        if long_term:
            markdown_output += "### Long Term (Next 3 Months)\n"
            for item in long_term:
                markdown_output += f"- {item}\n"
        markdown_output += "\n"

    # Performance Insight
    insight = analysis.get("performance_insight", "")
    if insight:
        markdown_output += f"## 💡 Performance Insight\n{insight}\n"

    return markdown_output
