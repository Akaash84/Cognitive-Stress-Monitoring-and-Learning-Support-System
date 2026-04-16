import os
from typing import Any, Dict, List, Optional, Tuple

import joblib

MODEL_PATH = os.path.join("model", "cognitive_model.pkl")

_payload = joblib.load(MODEL_PATH)
_model = _payload["model"]
_features: List[str] = _payload["features"]
_medians: Dict[str, float] = _payload.get("medians", {})


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _recommendations(features: Dict[str, float], predicted_label: str) -> List[str]:
    """
    Lightweight recommendation layer.
    You can replace this with a dedicated recommender later.
    """
    recs: List[str] = []

    logical = features.get("logical")
    mathematical = features.get("mathematical")
    verbal = features.get("verbal")
    memory = features.get("memory")

    # Domain-driven tips
    domain_scores = [
        ("Logical reasoning", logical),
        ("Mathematical aptitude", mathematical),
        ("Verbal ability", verbal),
        ("Working memory", memory),
    ]
    domain_scores = [(name, score) for name, score in domain_scores if score is not None]
    domain_scores.sort(key=lambda x: (x[1] is None, x[1]))

    if domain_scores:
        weakest = [name for name, _ in domain_scores[:2]]
        recs.append(f"Focus next week: {', '.join(weakest)} (lowest scoring areas).")

    # Stress / hardware signals
    hr = features.get("heart_rate_bpm")
    stress = features.get("stress_level")
    if hr is not None and hr >= 95:
        recs.append("Stress signal: high heart rate detected. Add 2-minute box-breathing before each section.")
    if stress is not None and stress >= 0.7:
        recs.append("Stress signal: elevated stress level. Use timed practice with short breaks (Pomodoro 25/5).")

    # Label-driven guidance
    label = (predicted_label or "").lower()
    if "poor" in label:
        recs.append("Start with foundation drills: accuracy first, then speed. Target 60%+ consistently.")
    elif "average" in label:
        recs.append("Build consistency: 2 mock tests/week + review wrong answers to improve patterns.")
    elif "good" in label:
        recs.append("Push to advanced: increase difficulty and add strict timing to reduce hesitation.")
    elif "excellent" in label:
        recs.append("Maintain peak performance: mixed-domain full mocks + fine-tune time allocation per section.")

    return recs[:6]


def predict_with_recommendations(
    *,
    logical: float,
    mathematical: float,
    verbal: float,
    memory: float,
    heart_rate_bpm: Optional[float] = None,
    stress_level: Optional[float] = None,
    hrv_ms: Optional[float] = None,
) -> Tuple[str, List[str]]:
    """
    Predict a performance label and return recommendations.

    Notes
    - The model will use only the feature columns it was trained with.
    - If you haven't added hardware columns to dataset.csv + retrained, they won't affect predictions yet,
      but we still use them in the recommendation layer.
    """
    raw: Dict[str, Optional[float]] = {
        "logical": logical,
        "mathematical": mathematical,
        "verbal": verbal,
        "memory": memory,
        "heart_rate_bpm": heart_rate_bpm,
        "stress_level": stress_level,
        "hrv_ms": hrv_ms,
    }

    # Build model input vector in the trained feature order
    row: List[float] = []
    used: Dict[str, float] = {}
    for f in _features:
        val_any = raw.get(f)
        if val_any is None:
            val = float(_medians.get(f, 0.0))
        else:
            val = float(val_any)
        row.append(val)
        used[f] = val

    predicted = _model.predict([row])[0]

    # Pass the full feature dict (including hardware) to recommender
    used_for_recs: Dict[str, float] = {k: float(v) for k, v in raw.items() if v is not None}
    recs = _recommendations(used_for_recs, str(predicted))
    return str(predicted), recs


# Backwards-compatible wrapper (old signature)
def predict_status(memory: float, concentration: float, digit: float, self_report: float) -> Any:
    """
    Deprecated: kept to avoid breaking older imports.
    Maps old inputs into the new API with best-effort mapping.
    """
    predicted, _ = predict_with_recommendations(
        logical=concentration,
        mathematical=digit,
        verbal=self_report,
        memory=memory,
    )
    return predicted