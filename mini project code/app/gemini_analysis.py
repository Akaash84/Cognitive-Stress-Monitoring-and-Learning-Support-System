"""
Groq-based stress analysis for cognitive assessment results.
Replaces previous Gemini (genai) usage with a minimal Groq HTTP client.
"""

import json
import os
from typing import Any, Dict, List, Optional

# local groq wrapper
try:
    # relative import when used as a package
    from .groq_client import GroqClient
except Exception:
    # fallback when run as a script from the same folder
    from groq_client import GroqClient


def _get_api_key() -> Optional[str]:
    """
    Retrieve API key for Groq (or legacy Gemini) from environment or Streamlit secrets.
    Priority:
      1. GROQ_API_KEY env
      2. GEMINI_API_KEY env (backwards compat)
      3. Streamlit secrets GROQ_API_KEY or GEMINI_API_KEY
    """
    # Prefer explicit Groq key
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()

    # Try Streamlit secrets if available
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and st.secrets:
            for key_name in ["GROQ_API_KEY", "groq_api_key", "GEMINI_API_KEY", "gemini_api_key", "API_KEY"]:
                api_key = st.secrets.get(key_name)
                if api_key and isinstance(api_key, str) and api_key.strip():
                    return api_key.strip()
    except Exception:
        pass

    return None


def load_questions_from_json(qids: List[str]) -> Dict[str, Any]:
    """
    Load questions from questions.json and return matched questions.
    """
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "questions.json")
    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            all_questions = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load questions.json: {str(e)}", "matched_questions": []}

    matched_questions = []
    qid_set = set(q.strip().upper() for q in qids if q)

    for category, difficulty_dict in all_questions.items():
        if isinstance(difficulty_dict, dict):
            for difficulty, questions_list in difficulty_dict.items():
                if isinstance(questions_list, list):
                    for q in questions_list:
                        qid = str(q.get("id", "")).strip().upper()
                        if qid in qid_set:
                            mq = {
                                "category": category,
                                "difficulty": difficulty,
                                "type": q.get("type", "unknown"),
                                "question": q.get("question", ""),
                                "answer": q.get("answer", "")
                            }
                            matched_questions.append(mq)

    return {
        "matched_questions": matched_questions,
        "total_matched": len(matched_questions),
        "total_requested": len(qids),
    }


def _local_analyze(questions_data: Dict[str, Any], health_summary: Dict[str, Any], score_percentage: float, time_taken_seconds: int, test_type: str) -> Dict[str, Any]:
    """Deterministic local analyzer used when no Groq API key is present.

    This function inspects question categories and simple health metrics to
    produce a structured analysis resembling the AI output.
    """
    matched = questions_data.get("matched_questions", [])

    # Count categories
    from collections import Counter
    cats = [q.get("category", "unknown") for q in matched]
    cat_counts = Counter(cats)

    # Determine overall stress level heuristically
    avg_stress = health_summary.get("avg_stress")
    if isinstance(avg_stress, (int, float)):
        if avg_stress >= 7 or score_percentage < 40:
            stress_level = "high"
            stress_score = min(10, round(avg_stress))
        elif avg_stress >= 4 or score_percentage < 70:
            stress_level = "moderate"
            stress_score = min(10, max(4, round(avg_stress)))
        else:
            stress_level = "low"
            stress_score = min(10, max(0, round(avg_stress)))
    else:
        # fallback to score-based
        if score_percentage < 40:
            stress_level = "high"
            stress_score = 8
        elif score_percentage < 70:
            stress_level = "moderate"
            stress_score = 5
        else:
            stress_level = "low"
            stress_score = 2

    # Problem areas: top 3 categories
    problem_areas = []
    for cat, cnt in cat_counts.most_common(3):
        problem_areas.append({
            "category": cat,
            "question_count": int(cnt),
            "impact": f"{cnt} question(s)",
            "stress_factor": "performance" if score_percentage < 70 else "uncategorized",
            "suggested_action": f"Focused practice on {cat} with targeted problem sets."
        })

    # Topic recommendations: suggest studying top categories with actionable plan
    topic_recommendations = []
    for cat, cnt in cat_counts.most_common(5):
        priority = "high" if cnt >= 2 else "medium"
        topic_recommendations.append({
            "topic": cat,
            "priority": priority,
            "reason": f"Found {cnt} question(s) in this domain during stressed periods",
            "suggested_action": {
                "overview": f"Study {cat} fundamentals and practice problems.",
                "plan": [
                    f"Week 1: Review core concepts for {cat} (30-45 min daily)",
                    f"Week 2-3: Complete 5 targeted practice sets for {cat}",
                    f"Week 4: Take timed mini-test focused on {cat}"
                ],
                "expected_outcome": "Improve accuracy and reduce time-per-question"
            }
        })

    # Coping strategies (generic but actionable)
    coping_strategies = [
        {"strategy": "Pomodoro study cycles", "description": "Use 25/5 minute cycles during practice to maintain focus.", "expected_benefit": "Increase sustained concentration and reduce anxiety"},
        {"strategy": "Simulated timed practice", "description": "Do short timed quizzes to build confidence under pressure.", "expected_benefit": "Reduce test-time stress and improve pacing"},
    ]

    # Personalized suggestions based on short/medium/long term
    personalized_suggestions = {
        "short_term": [],
        "medium_term": [],
        "long_term": []
    }

    # Build personalized suggestions from top topics
    for topic in topic_recommendations[:3]:
        personalized_suggestions["short_term"].append(f"Spend 20-30 minutes daily on {topic['topic']} for one week.")
        personalized_suggestions["medium_term"].append(f"Complete 10 targeted practice questions for {topic['topic']} each week for next month.")
        personalized_suggestions["long_term"].append(f"Reassess {topic['topic']} performance after 3 months and adjust learning plan.")

    overall = {
        "overall_stress_analysis": {"stress_level": stress_level, "stress_score": stress_score, "summary": f"Heuristic analysis: {stress_level} stress."},
        "problem_areas": problem_areas,
        "topic_recommendations": topic_recommendations,
        "coping_strategies": coping_strategies,
        "personalized_suggestions": personalized_suggestions,
        "performance_insight": f"Score: {score_percentage:.1f}% | Time: {time_taken_seconds//60}m",
        "total_requested": questions_data.get("total_requested", len(matched)),
        "total_matched": questions_data.get("total_matched", len(matched)),
        "matched_questions": matched
    }

    return overall


def analyze_stress_with_gemini(
    hsqsns: List[str],
    health_summary: Dict[str, Any],
    test_score: float,
    max_score: float,
    time_taken_seconds: int,
    test_type: str = "foundation",
) -> Dict[str, Any]:
    """
    Compatibility wrapper: if GROQ_API_KEY is present, send request to Groq; otherwise
    use local deterministic analyzer so the app works without an API key.
    """
    api_key = _get_api_key()

    # Load questions
    questions_data = load_questions_from_json(hsqsns)
    if "error" in questions_data:
        return {"status": "error", "error": questions_data["error"]}

    score_percentage = (test_score / max_score * 100) if max_score > 0 else 0

    # If no API key, try HF local model for dynamic output, else use local analyzer
    if not api_key:
        try:
            from .hf_client import HFClient
            hf = HFClient()

            # Build a strict instruction for HF to return JSON only.
            prompt = (
                "You are an expert educational psychologist. "
                "Given the following list of questions (with categories) and a short health summary, "
                "return a SINGLE valid JSON object (no extra commentary) with the keys: "
                "overall_stress_analysis, problem_areas, topic_recommendations, coping_strategies, "
                "personalized_suggestions, performance_insight, total_requested, total_matched, matched_questions. "
                "- overall_stress_analysis: {stress_level (low/moderate/high), stress_score (0-10), summary} \n"
                "- problem_areas: array of {category, question_count, impact, suggested_action} ordered by priority\n"
                "- topic_recommendations: array of {topic, priority, reason, suggested_action}\n"
                "- coping_strategies: array of short actionable strategies\n"
                "- personalized_suggestions: object with short_term, medium_term, long_term arrays\n"
                "- performance_insight: string\n"
                "- total_requested: integer (number of qids input)\n"
                "- total_matched: integer (number of matched questions found)\n"
                "- matched_questions: array of objects {qid, category, question}\n\n"
            )
            prompt += f"Questions:\n{q_texts}\nHealthSummary:{json.dumps(health_summary)}\nScorePercentage:{score_percentage:.1f}\n"

            hf_resp = hf.generate(prompt, max_length=1024)
            text = hf_resp.get("text") if isinstance(hf_resp, dict) else None

            # Try robust JSON parsing with up to two attempts
            parsed = None
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                except Exception:
                    # try extract first JSON object substring
                    try:
                        s = text
                        start = s.find('{')
                        end = s.rfind('}')
                        if start != -1 and end != -1 and end > start:
                            candidate = s[start:end+1]
                            parsed = json.loads(candidate)
                    except Exception:
                        parsed = None

            # If parse failed, retry with a stricter instruction
            if parsed is None and isinstance(text, str):
                retry_prompt = "Return ONLY a single valid JSON object (no text) that matches the requested schema.\nPrevious output:\n" + text + "\nNow produce only the JSON object."
                try:
                    hf_resp2 = hf.generate(retry_prompt, max_length=1024)
                    text2 = hf_resp2.get("text") if isinstance(hf_resp2, dict) else None
                    if isinstance(text2, str):
                        try:
                            parsed = json.loads(text2)
                        except Exception:
                            # try substring
                            try:
                                s = text2
                                start = s.find('{')
                                end = s.rfind('}')
                                if start != -1 and end != -1 and end > start:
                                    candidate = s[start:end+1]
                                    parsed = json.loads(candidate)
                            except Exception:
                                parsed = None
                except Exception:
                    parsed = None

            # Validate and normalize parsed JSON
            if isinstance(parsed, dict):
                # ensure matched_questions data exists and counts are correct
                matched_list = questions_data.get("matched_questions", [])
                parsed_total_matched = parsed.get("total_matched")
                if parsed_total_matched is None or int(parsed_total_matched) != len(matched_list):
                    parsed["total_matched"] = len(matched_list)

                parsed_total_requested = parsed.get("total_requested")
                if parsed_total_requested is None or int(parsed_total_requested) != len(hsqsns):
                    parsed["total_requested"] = len(hsqsns)

                # ensure matched_questions array present
                if "matched_questions" not in parsed or not isinstance(parsed.get("matched_questions"), list):
                    # inject minimal matched_questions
                    parsed["matched_questions"] = [
                        {"qid": q.get("qid") or q.get("id") or "", "category": q.get("category"), "question": q.get("question")}
                        for q in matched_list
                    ]

                # normalize problem_areas question_count using matched_questions
                from collections import Counter
                cat_counts = Counter([q.get("category") for q in matched_list if q.get("category")])
                pas = parsed.get("problem_areas")
                if isinstance(pas, list):
                    for pa in pas:
                        cat = pa.get("category")
                        if cat and ("question_count" not in pa or not isinstance(pa.get("question_count"), int)):
                            pa["question_count"] = int(cat_counts.get(cat, 0))

                # Ensure topic_recommendations have actionable suggested_action objects
                tr = parsed.get("topic_recommendations")
                if isinstance(tr, list):
                    for t in tr:
                        if isinstance(t.get("suggested_action"), str):
                            t["suggested_action"] = {"overview": t.get("suggested_action"), "plan": [f"Practice 5 problems in {t.get('topic')}"]}

                return {"status": "ok", "analysis": parsed}

        except Exception:
            # transformers not available or error - fall back
            pass

        analysis = _local_analyze(questions_data, health_summary, score_percentage, time_taken_seconds, test_type)
        return {"status": "ok", "analysis": analysis}

    # If API key present, attempt Groq call
    try:
        try:
            from .groq_client import GroqClient
        except Exception:
            from groq_client import GroqClient

        client = GroqClient(api_key=api_key)

        # build prompt summarizing inputs
        q_texts = "\n\n".join([f"{i+1}. ({q.get('category')}) {q.get('question')}" for i, q in enumerate(questions_data.get("matched_questions", []) ) ])
        prompt = f"Provide a JSON analysis of the user's stress given the following data.\nTest Type: {test_type}\nScore: {test_score}/{max_score} ({score_percentage:.1f}%)\nTime Taken (s): {time_taken_seconds}\nHealth Summary: {json.dumps(health_summary)}\nQuestions:\n{q_texts}\n\nReturn JSON with keys: overall_stress_analysis, problem_areas, topic_recommendations, coping_strategies, personalized_suggestions, performance_insight."

        resp = client.generate(prompt, model=os.getenv("GROQ_MODEL", "llama3-8b-8192"))
        # client.generate returns dict with 'text' or raw shapes depending on implementation
        # try to extract text
        if isinstance(resp, dict) and resp.get("text"):
            text = resp.get("text")
        elif isinstance(resp, dict) and "raw" in resp:
            # Prefer client's extractor if available
            extractor = getattr(client, "_extract_text_from_response", None)
            if callable(extractor):
                text = extractor(resp.get("raw", {}))
            else:
                # Fallback manual extraction from common shapes
                raw = resp.get("raw", {})
                text = None
                if isinstance(raw, dict):
                    choices = raw.get("choices")
                    if isinstance(choices, list) and choices:
                        first = choices[0]
                        if isinstance(first, dict):
                            msg = first.get("message")
                            if isinstance(msg, dict):
                                text = msg.get("content")
                            else:
                                text = first.get("text") or first.get("output")
                    if text is None:
                        text = raw.get("output") or raw.get("generated_text")
                if text is None:
                    text = str(raw)
        else:
            text = str(resp)

        # attempt parse
        try:
            parsed = json.loads(text)
            return {"status": "ok", "analysis": parsed}
        except Exception:
            return {"status": "partial", "raw_analysis": text}

    except Exception as e:
        # Fall back to local analyzer on any Groq failure
        analysis = _local_analyze(questions_data, health_summary, score_percentage, time_taken_seconds, test_type)
        analysis["note"] = f"fallback_local_due_to: {str(e)}"
        return {"status": "ok", "analysis": analysis}


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

    stress_info = analysis.get("overall_stress_analysis", {})
    stress_level = stress_info.get("stress_level", "unknown").upper()
    stress_score = stress_info.get("stress_score", "N/A")
    markdown_output += f"""## Overall Stress Assessment
- **Stress Level**: {stress_level}
- **Stress Score**: {stress_score}/10
- **Summary**: {stress_info.get('summary', 'N/A')}

"""

    problem_areas = analysis.get("problem_areas", [])
    if problem_areas:
        markdown_output += "## 🎯 Problem Areas\n"
        for area in problem_areas:
            markdown_output += f"- **{area.get('category')}** (Impact: {area.get('impact')})\n"
            markdown_output += f"  - {area.get('stress_factor', 'N/A')}\n"
        markdown_output += "\n"

    topics = analysis.get("topic_recommendations", [])
    if topics:
        markdown_output += "## 📚 Topics to Focus On\n"
        for topic in topics:
            markdown_output += f"- **{topic.get('topic')}** (Priority: {topic.get('priority')})\n"
            markdown_output += f"  - *Reason*: {topic.get('reason', 'N/A')}\n"
            markdown_output += f"  - *Action*: {topic.get('suggested_action', 'N/A')}\n"
        markdown_output += "\n"

    strategies = analysis.get("coping_strategies", [])
    if strategies:
        markdown_output += "## 💪 Coping Strategies\n"
        for strategy in strategies:
            markdown_output += f"- **{strategy.get('strategy')}**: {strategy.get('description', 'N/A')}\n"
            markdown_output += f"  - Expected benefit: {strategy.get('expected_benefit', 'N/A')}\n"
        markdown_output += "\n"

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

    insight = analysis.get("performance_insight", "")
    if insight:
        markdown_output += f"## 💡 Performance Insight\n{insight}\n"

    return markdown_output
