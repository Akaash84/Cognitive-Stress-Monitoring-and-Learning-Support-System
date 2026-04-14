import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

DATASET_PATH = "data/dataset.csv"
MODEL_PATH = "model/cognitive_model.pkl"

# Columns we WANT the model to understand.
# If your dataset doesn't contain some (e.g. hardware signals), they will be ignored during training
# until you add them to the dataset and retrain.
REQUESTED_FEATURES = [
    # domain scores (0-5 or 0-100, depending on your dataset)
    "logical",
    "mathematical",
    "verbal",
    "memory",
    # optional: hardware / stress signals (add these columns to dataset.csv to train with them)
    "heart_rate_bpm",
    "stress_level",
    "hrv_ms",
]


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def main() -> None:
    data = pd.read_csv(DATASET_PATH)
    if "label" not in data.columns:
        raise ValueError("dataset.csv must contain a 'label' column.")

    available_features = [c for c in REQUESTED_FEATURES if c in data.columns]
    if not available_features:
        raise ValueError(
            f"None of the requested feature columns are present in {DATASET_PATH}. "
            f"Expected at least one of: {REQUESTED_FEATURES}"
        )

    data = _coerce_numeric(data, available_features)

    # Simple missing-value handling: fill with median of each feature.
    medians = {col: float(data[col].median()) for col in available_features}
    X = data[available_features].fillna(medians)
    y = data["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test) if len(X_test) else float("nan")
    print("Model features:", available_features)
    print("Model Accuracy:", accuracy)

    payload = {
        "model": model,
        "features": available_features,
        "medians": medians,
        "label_classes": sorted(y.dropna().unique().tolist()),
    }
    joblib.dump(payload, MODEL_PATH)
    print("Model saved successfully to", MODEL_PATH)


if __name__ == "__main__":
    main()