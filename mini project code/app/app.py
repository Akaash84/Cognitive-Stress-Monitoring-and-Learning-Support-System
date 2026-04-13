#trail 1 best
import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import re
import pandas as pd
import altair as alt
from login import create_user, login_user
from question_generator import (
    generate_test,
    run 
)

st.set_page_config(page_title="Cognitive Assessment System", layout="wide")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = PROJECT_ROOT / "data" / "images"


def _normalize_answer_token(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def _resolve_question_image_path(image_ref):
    if not image_ref:
        return None

    if not IMAGES_DIR.exists():
        return None

    raw_name = Path(str(image_ref)).name
    stem = Path(raw_name).stem
    suffix = Path(raw_name).suffix or ".png"

    candidates = {raw_name}

    compact_stem = stem.replace("-", "")
    match_with_option = re.match(r"^([A-Za-z]+)(\d+)([A-Za-z])$", compact_stem)
    if match_with_option:
        prefix, number, option = match_with_option.groups()
        candidates.update(
            {
                f"{prefix}{number}{option}{suffix}",
                f"{prefix}{number}-{option}{suffix}",
                f"{prefix}-{number}{option}{suffix}",
                f"{prefix}-{number}-{option}{suffix}",
            }
        )

    match_plain = re.match(r"^([A-Za-z]+)(\d+)$", compact_stem)
    if match_plain:
        prefix, number = match_plain.groups()
        candidates.update({f"{prefix}{number}{suffix}", f"{prefix}-{number}{suffix}"})

    existing_by_lower = {}
    for path in IMAGES_DIR.iterdir():
        if path.is_file():
            existing_by_lower[path.name.lower()] = path

    for candidate in candidates:
        matched = existing_by_lower.get(candidate.lower())
        if matched is not None:
            return matched

    return None


def _is_mcq_answer_correct(question, user_answer, correct_answer):
    """Compare MCQ answers while supporting both keyed and value-style answer keys."""
    if user_answer is None or correct_answer is None:
        return False

    if _normalize_answer_token(user_answer) == _normalize_answer_token(correct_answer):
        return True

    options = question.get("options")
    if isinstance(options, dict):
        for key, value in options.items():
            if (
                _normalize_answer_token(correct_answer) == _normalize_answer_token(key)
                and _normalize_answer_token(user_answer) == _normalize_answer_token(value)
            ):
                return True
            if (
                _normalize_answer_token(user_answer) == _normalize_answer_token(key)
                and _normalize_answer_token(correct_answer) == _normalize_answer_token(value)
            ):
                return True

    return False


def _build_option_items(options):
    option_items = []
    if isinstance(options, dict):
        iterable = list(options.items())
    elif isinstance(options, list):
        iterable = [(chr(65 + idx), value) for idx, value in enumerate(options)]
    else:
        iterable = []

    for key, value in iterable:
        image_path = _resolve_question_image_path(value) if isinstance(value, str) else None
        # Show only the option value (no 'A) ' prefix). For image options, use a neutral label.
        if image_path is not None:
            label = "Image option"
        else:
            label = f"{value}"

        option_items.append(
            {
                "key": str(key),
                "value": value,
                "label": label,
                "image_path": image_path,
            }
        )

    return option_items


def render_proctor_component(exam_active, strict_mode=True):
    state_text = "active" if exam_active else "inactive"
    strict_text = "true" if strict_mode else "false"
    components.html(
                f"""
                <div id="proctor-shell" style="border:1px solid #d9e2ec;border-radius:12px;padding:8px;margin:4px 0 10px auto;background:#f8fbff;max-width:320px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
                        <div style="font-weight:700;color:#102A43;">Proctoring Monitor</div>
                        <div id="proctor-status" style="font-size:12px;padding:4px 10px;border-radius:999px;background:#dbeafe;color:#1e3a8a;">Preparing...</div>
                    </div>
                    <div id="proctor-alert" style="display:none;margin-top:8px;padding:8px;border-radius:8px;background:#fee2e2;color:#991b1b;font-weight:600;">
                        No face detected. Please face the camera.
                    </div>
                    <video id="proctor-video" autoplay playsinline muted style="margin-top:8px;width:100%;max-height:150px;border-radius:10px;background:#0b1726;"></video>
                    <div id="proctor-footnote" style="margin-top:8px;font-size:12px;color:#334155;">Camera and recording run only while exam mode is active.</div>
                    <div id="proctor-violations" style="margin-top:6px;font-size:12px;color:#7c2d12;">Tab switch violations: 0</div>
                    <div id="proctor-download" style="margin-top:8px;"></div>
                </div>

                <script>
                (() => {{
                    const examState = "{state_text}";
                    const strictMode = {strict_text};
                    const parentWindow = window.parent;
                    const statusEl = document.getElementById("proctor-status");
                    const alertEl = document.getElementById("proctor-alert");
                    const videoEl = document.getElementById("proctor-video");
                    const violationsEl = document.getElementById("proctor-violations");
                    const downloadEl = document.getElementById("proctor-download");

                    if (!parentWindow.__examProctorState) {{
                        parentWindow.__examProctorState = {{
                            stream: null,
                            recorder: null,
                            chunks: [],
                            faceTimer: null,
                            misses: 0,
                            detectorSupported: ("FaceDetector" in window),
                            detectorMode: null,
                            blazeModel: null,
                            tfLoadingPromise: null,
                            recordingUrl: null,
                            fullscreenListener: null,
                            tabSwitches: 0,
                            blurHandler: null,
                            visibilityHandler: null,
                            sessionInitialized: false,
                        }};
                    }}

                    const state = parentWindow.__examProctorState;

                    const setViolationsCounter = (value) => {{
                        violationsEl.textContent = `Tab switch violations: ${{value}}`;
                        try {{
                            const url = new URL(parentWindow.location.href);
                            url.searchParams.set("violations", String(value));
                            parentWindow.history.replaceState({{}}, "", url.toString());
                        }} catch (e) {{
                            // Ignore query param update failures.
                        }}
                    }};

                    const registerTabSwitch = () => {{
                        state.tabSwitches += 1;
                        setViolationsCounter(state.tabSwitches);
                        if (strictMode && state.tabSwitches >= 3) {{
                            alertEl.style.display = "block";
                            alertEl.textContent = "Alert: Tab/window switch detected. Stay on the exam screen.";
                        }}
                    }};

                    const renderDownload = () => {{
                        if (state.recordingUrl) {{
                            downloadEl.innerHTML = `<a href="${{state.recordingUrl}}" download="exam-recording.webm" style="display:inline-block;background:#1d4ed8;color:#fff;text-decoration:none;padding:6px 10px;border-radius:8px;font-size:12px;">Download Exam Recording</a>`;
                        }} else {{
                            downloadEl.innerHTML = "";
                        }}
                    }};

                    const safeExitFullscreen = async () => {{
                        try {{
                            const doc = parentWindow.document;
                            if (doc.fullscreenElement) {{
                                await doc.exitFullscreen();
                            }}
                        }} catch (e) {{
                            // Ignore fullscreen API failures.
                        }}
                    }};

                    const stopAll = async () => {{
                        try {{
                            if (state.faceTimer) {{
                                clearInterval(state.faceTimer);
                                state.faceTimer = null;
                            }}

                            if (state.recorder && state.recorder.state !== "inactive") {{
                                await new Promise((resolve) => {{
                                    state.recorder.onstop = resolve;
                                    state.recorder.stop();
                                }});
                            }}

                            if (state.chunks && state.chunks.length > 0) {{
                                const blob = new Blob(state.chunks, {{ type: "video/webm" }});
                                state.recordingUrl = URL.createObjectURL(blob);
                                state.chunks = [];
                            }}

                            if (state.stream) {{
                                state.stream.getTracks().forEach((track) => track.stop());
                                state.stream = null;
                            }}

                            if (state.fullscreenListener) {{
                                parentWindow.document.removeEventListener("fullscreenchange", state.fullscreenListener);
                                state.fullscreenListener = null;
                            }}

                            if (state.blurHandler) {{
                                parentWindow.removeEventListener("blur", state.blurHandler);
                                state.blurHandler = null;
                            }}

                            if (state.visibilityHandler) {{
                                parentWindow.document.removeEventListener("visibilitychange", state.visibilityHandler);
                                state.visibilityHandler = null;
                            }}

                            state.sessionInitialized = false;

                            await safeExitFullscreen();
                            statusEl.textContent = "Exam ended";
                            statusEl.style.background = "#dcfce7";
                            statusEl.style.color = "#166534";
                            alertEl.style.display = "none";
                            renderDownload();
                        }} catch (err) {{
                            statusEl.textContent = "Proctor stop error";
                            statusEl.style.background = "#fee2e2";
                            statusEl.style.color = "#991b1b";
                        }}
                    }};

                    const detectFaceLoop = async () => {{
                        const withTimeout = (promise, ms) =>
                            Promise.race([
                                promise,
                                new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
                            ]);

                        const loadScript = (src) => new Promise((resolve, reject) => {{
                            const existing = parentWindow.document.querySelector(`script[src="${{src}}"]`);
                            if (existing) {{
                                if (existing.dataset.loaded === "true") {{
                                    resolve();
                                    return;
                                }}
                                existing.addEventListener("load", () => resolve(), {{ once: true }});
                                existing.addEventListener("error", () => reject(new Error("Script load failed")), {{ once: true }});
                                return;
                            }}

                            const script = parentWindow.document.createElement("script");
                            script.src = src;
                            script.async = true;
                            script.onload = () => {{
                                script.dataset.loaded = "true";
                                resolve();
                            }};
                            script.onerror = () => reject(new Error("Script load failed"));
                            parentWindow.document.head.appendChild(script);
                        }});

                        const loadScriptAny = async (sources) => {{
                            let lastError = null;
                            for (const src of sources) {{
                                try {{
                                    await withTimeout(loadScript(src), 12000);
                                    return true;
                                }} catch (err) {{
                                    lastError = err;
                                }}
                            }}
                            throw lastError || new Error("No script source loaded");
                        }};

                        const initBlazeFaceDetector = async () => {{
                            if (state.blazeModel) return state.blazeModel;
                            if (!state.tfLoadingPromise) {{
                                state.tfLoadingPromise = (async () => {{
                                    if (!parentWindow.tf) {{
                                        await loadScriptAny([
                                            "https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js",
                                            "https://unpkg.com/@tensorflow/tfjs@4.22.0/dist/tf.min.js",
                                        ]);
                                    }}
                                    if (!parentWindow.blazeface) {{
                                        await loadScriptAny([
                                            "https://cdn.jsdelivr.net/npm/@tensorflow-models/blazeface@0.1.0/dist/blazeface.min.js",
                                            "https://unpkg.com/@tensorflow-models/blazeface@0.1.0/dist/blazeface.min.js",
                                        ]);
                                    }}
                                    state.blazeModel = await parentWindow.blazeface.load();
                                    return state.blazeModel;
                                }})();
                            }}
                            try {{
                                return await state.tfLoadingPromise;
                            }} catch (e) {{
                                return null;
                            }}
                        }};

                        let nativeDetector = null;
                        let blazeModel = null;

                        if (state.detectorSupported) {{
                            try {{
                                nativeDetector = new FaceDetector({{ fastMode: true, maxDetectedFaces: 1 }});
                                state.detectorMode = "native";
                            }} catch (e) {{
                                state.detectorMode = null;
                            }}
                        }}

                        if (!state.detectorMode) {{
                            statusEl.textContent = "Loading fallback face detector...";
                            statusEl.style.background = "#ffedd5";
                            statusEl.style.color = "#9a3412";
                            blazeModel = await initBlazeFaceDetector();
                            if (!blazeModel) {{
                                statusEl.textContent = "Recording active (Face detection unavailable: allow internet/CDN or use Chrome/Edge latest)";
                                statusEl.style.background = "#ffedd5";
                                statusEl.style.color = "#9a3412";
                                return;
                            }}
                            state.detectorMode = "blazeface";
                        }}

                        state.faceTimer = setInterval(async () => {{
                            try {{
                                if (!videoEl.videoWidth || !videoEl.videoHeight) return;
                                let hasFace = false;

                                if (state.detectorMode === "native" && nativeDetector) {{
                                    const faces = await nativeDetector.detect(videoEl);
                                    hasFace = !!(faces && faces.length > 0);
                                }} else if (state.detectorMode === "blazeface" && blazeModel) {{
                                    const preds = await blazeModel.estimateFaces(videoEl, false);
                                    hasFace = !!(preds && preds.length > 0);
                                }}

                                if (!hasFace) {{
                                    state.misses += 1;
                                    if (state.misses >= 2) {{
                                        alertEl.style.display = "block";
                                        statusEl.textContent = "Alert: No face detected";
                                        statusEl.style.background = "#fee2e2";
                                        statusEl.style.color = "#991b1b";
                                    }}
                                }} else {{
                                    state.misses = 0;
                                    alertEl.style.display = "none";
                                    if (state.detectorMode === "blazeface") {{
                                        statusEl.textContent = "Recording active | Face detected (fallback)";
                                    }} else {{
                                        statusEl.textContent = "Recording active | Face detected";
                                    }}
                                    statusEl.style.background = "#dbeafe";
                                    statusEl.style.color = "#1e3a8a";
                                }}
                            }} catch (e) {{
                                // Ignore detection frame errors.
                            }}
                        }}, 1800);
                    }};

                    const startAll = async () => {{
                        try {{
                            const doc = parentWindow.document;
                            if (strictMode && !doc.fullscreenElement) {{
                                await doc.documentElement.requestFullscreen();
                            }}

                            if (!state.sessionInitialized) {{
                                state.tabSwitches = 0;
                                setViolationsCounter(0);
                                state.sessionInitialized = true;
                            }}

                            if (!state.stream) {{
                                state.stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                            }}
                            videoEl.srcObject = state.stream;

                            if (!state.recorder || state.recorder.state === "inactive") {{
                                state.chunks = [];
                                state.recorder = new MediaRecorder(state.stream, {{ mimeType: "video/webm" }});
                                state.recorder.ondataavailable = (event) => {{
                                    if (event.data && event.data.size > 0) {{
                                        state.chunks.push(event.data);
                                    }}
                                }};
                                state.recorder.start(1000);
                            }}

                            if (!state.fullscreenListener) {{
                                state.fullscreenListener = async () => {{
                                    if (strictMode && examState === "active" && !parentWindow.document.fullscreenElement) {{
                                        alertEl.style.display = "block";
                                        alertEl.textContent = "Fullscreen exited. Returning to fullscreen exam mode.";
                                        try {{
                                            await parentWindow.document.documentElement.requestFullscreen();
                                        }} catch (e) {{
                                            // Ignore browser restriction failures.
                                        }}
                                    }}
                                }};
                                parentWindow.document.addEventListener("fullscreenchange", state.fullscreenListener);
                            }}

                            if (strictMode && !state.blurHandler) {{
                                state.blurHandler = () => registerTabSwitch();
                                parentWindow.addEventListener("blur", state.blurHandler);
                            }}
                            if (strictMode && !state.visibilityHandler) {{
                                state.visibilityHandler = () => {{
                                    if (parentWindow.document.visibilityState === "hidden") {{
                                        registerTabSwitch();
                                    }}
                                }};
                                parentWindow.document.addEventListener("visibilitychange", state.visibilityHandler);
                            }}

                            statusEl.textContent = "Recording active";
                            statusEl.style.background = "#dbeafe";
                            statusEl.style.color = "#1e3a8a";
                            setViolationsCounter(state.tabSwitches);
                            renderDownload();
                            await detectFaceLoop();
                        }} catch (err) {{
                            statusEl.textContent = "Camera permission required";
                            statusEl.style.background = "#fee2e2";
                            statusEl.style.color = "#991b1b";
                            alertEl.style.display = "block";
                            alertEl.textContent = "Allow camera/microphone to continue proctored exam mode.";
                        }}
                    }};

                    if (examState === "active") {{
                        startAll();
                    }} else {{
                        stopAll();
                    }}

                    renderDownload();
                }})();
                </script>
                """,
                height=280,
                scrolling=False,
        )


def init_state():
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "questions" not in st.session_state:
        st.session_state.questions = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "score" not in st.session_state:
        st.session_state.score = None
    if "test_submitted" not in st.session_state:
        st.session_state.test_submitted = False
    if "test_start_time" not in st.session_state:
        st.session_state.test_start_time = None
    if "test_duration_seconds" not in st.session_state:
        st.session_state.test_duration_seconds = 25 * 60
    if "auto_submitted" not in st.session_state:
        st.session_state.auto_submitted = False
    if "time_taken_seconds" not in st.session_state:
        st.session_state.time_taken_seconds = 0
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
    if "visited_questions" not in st.session_state:
        st.session_state.visited_questions = []
    if "submit_confirmation_text" not in st.session_state:
        st.session_state.submit_confirmation_text = ""
    if "attempted_questions" not in st.session_state:
        st.session_state.attempted_questions = 0
    if "submission_saved" not in st.session_state:
        st.session_state.submission_saved = False
    if "test_mode" not in st.session_state:
        st.session_state.test_mode = "Exam"
    if "review_rows" not in st.session_state:
        st.session_state.review_rows = []
    if "max_score" not in st.session_state:
        st.session_state.max_score = 0.0
    if "score_breakdown" not in st.session_state:
        st.session_state.score_breakdown = {"positive": 0.0, "negative": 0.0, "partial": 0.0}
    if "tab_switch_violations" not in st.session_state:
        st.session_state.tab_switch_violations = 0


def apply_theme():
    st.markdown(
        """
        <style>
        .stApp {
            animation: pageFade 0.45s ease-out;
        }
        .stButton button,
        .stDownloadButton button,
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] {
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease, background-color 0.25s ease;
        }
        .stButton button:hover,
        .stDownloadButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.12);
        }
        .stMetric {
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .stMetric:hover {
            transform: translateY(-3px);
        }
        .app-header {
            background: linear-gradient(90deg, #102A43, #243B53);
            color: white;
            border-radius: 10px;
            padding: 10px 18px;
            margin-bottom: 12px;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
            animation: fadeUp 0.55s ease-out;
        }
        .home-card {
            background: #f7f9fb;
            border: 1px solid #d4dbe3;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }
        .hero-panel {
            background: linear-gradient(135deg, #0f2740 0%, #1f3f5b 52%, #5f7d99 100%);
            color: #ffffff;
            border-radius: 18px;
            padding: 28px;
            margin-bottom: 18px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
            animation: fadeUp 0.7s ease-out;
            position: relative;
            overflow: hidden;
        }
        .hero-panel::after {
            content: "";
            position: absolute;
            top: -40px;
            right: -60px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(255,255,255,0.14), rgba(255,255,255,0));
            border-radius: 50%;
            animation: floatOrb 7s ease-in-out infinite;
        }
        .hero-panel::before {
            content: "";
            position: absolute;
            left: -40px;
            bottom: -80px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(255,255,255,0.10), rgba(255,255,255,0));
            border-radius: 50%;
            animation: floatOrb 9s ease-in-out infinite reverse;
        }
        .hero-kicker {
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.8rem;
            opacity: 0.85;
            margin-bottom: 8px;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 10px;
        }
        .hero-copy {
            font-size: 1rem;
            line-height: 1.7;
            max-width: 760px;
            opacity: 0.96;
            margin-bottom: 18px;
        }
        .hero-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .hero-tag {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #ffffff;
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 0.9rem;
            backdrop-filter: blur(6px);
            animation: fadeUp 0.9s ease-out;
            transition: transform 0.25s ease, background-color 0.25s ease, border-color 0.25s ease;
        }
        .hero-tag:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.18);
            border-color: rgba(255, 255, 255, 0.26);
        }
        .feature-card {
            background: linear-gradient(180deg, #e8f1fb 0%, #dce9f7 100%);
            border: 1px solid #abc2dc;
            border-radius: 16px;
            padding: 18px;
            min-height: 170px;
            box-shadow: 0 10px 20px rgba(20, 50, 77, 0.08);
            margin: 8px 0 26px 0;
            animation: fadeUp 0.8s ease-out;
            transition: transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease, background 0.35s ease;
        }
        .feature-card:hover {
            transform: translateY(-6px) scale(1.01);
            box-shadow: 0 18px 32px rgba(20, 50, 77, 0.14);
            border-color: #7fa3c7;
            background: linear-gradient(180deg, #edf5fd 0%, #deebf8 100%);
        }
        .feature-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #14324d, #365d7c);
            color: #ffffff;
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .feature-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #102A43;
            margin-bottom: 8px;
        }
        .feature-copy {
            color: #3f5f7d;
            line-height: 1.65;
            font-size: 0.96rem;
        }
        .section-panel {
            background: linear-gradient(180deg, #edf4fc 0%, #e0ebf8 100%);
            border: 1px solid #b1c8e0;
            border-radius: 16px;
            padding: 18px;
            margin: 10px 0 22px 0;
            animation: fadeUp 0.95s ease-out;
            box-shadow: 0 10px 20px rgba(20, 50, 77, 0.08);
            transition: transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
        }
        .section-panel:hover {
            transform: translateY(-4px);
            box-shadow: 0 16px 28px rgba(20, 50, 77, 0.12);
            border-color: #86a9cc;
        }
        .section-panel h4 {
            color: #173b5f;
            margin-bottom: 8px;
        }
        .section-panel p {
            color: #3f5f7d;
            line-height: 1.7;
            margin-bottom: 16px;
        }
        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(18px) scale(0.985);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes pageFade {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        @keyframes floatOrb {
            0% {
                transform: translateY(0px) translateX(0px);
            }
            50% {
                transform: translateY(-10px) translateX(8px);
            }
            100% {
                transform: translateY(0px) translateX(0px);
            }
        }
        .card-delay-1 {
            animation-delay: 0.08s;
            animation-fill-mode: both;
        }
        .card-delay-2 {
            animation-delay: 0.16s;
            animation-fill-mode: both;
        }
        .card-delay-3 {
            animation-delay: 0.24s;
            animation-fill-mode: both;
        }
        .card-delay-4 {
            animation-delay: 0.1s;
            animation-fill-mode: both;
        }
        .card-delay-5 {
            animation-delay: 0.2s;
            animation-fill-mode: both;
        }
        .exam-card {
            background: #f4f7fb;
            border: 1px solid #cfd9e6;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .exam-shell {
            background: #f8fbff;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 18px;
        }
        .exam-title {
            background: linear-gradient(90deg, #102A43, #243B53);
            color: #ffffff;
            border-radius: 10px;
            padding: 8px 12px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .palette-title {
            background: #243B53;
            color: #ffffff;
            border-radius: 8px;
            padding: 8px 10px;
            margin-bottom: 8px;
            font-weight: 600;
            text-align: center;
        }
        .question-text {
            font-size: 1.35rem;
            line-height: 1.8;
            font-weight: 600;
            margin-bottom: 16px;
        }
        [class*="st-key-submit_test_main"] button {
            background-color: #2e7d32 !important;
            border-color: #2e7d32 !important;
            color: #ffffff !important;
        }
        [class*="st-key-submit_test_main"] button:hover {
            background-color: #256628 !important;
            border-color: #256628 !important;
            color: #ffffff !important;
        }
        [class*="st-key-nav_login"] button,
        [class*="st-key-login_submit"] button {
            background-color: #f8b4b4 !important;
            border-color: #f8b4b4 !important;
            color: #7f1d1d !important;
        }
        [class*="st-key-nav_login"] button:hover,
        [class*="st-key-login_submit"] button:hover {
            background-color: #f28b8b !important;
            border-color: #f28b8b !important;
            color: #7f1d1d !important;
        }
        div[data-testid="stRadio"] label {
            font-size: 1.05rem !important;
        }
        div[data-testid="stRadio"] p {
            font-size: 1.05rem !important;
        }
        /* Make radio options visually distinct and show radio inline with text */
        div[data-testid="stRadio"] label {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 12px !important;
            padding: 10px 14px !important;
            border-radius: 10px !important;
            background: #f1f5f9 !important;
            margin: 8px 0 !important;
            border: 1px solid #e2e8f0 !important;
            min-height: 48px !important;
        }
        div[data-testid="stRadio"] label input[type="radio"] {
            margin: 0 !important;
            transform: scale(1.05) !important;
        }

        /* Number memory badge styling */
        .num-badge {
            display: inline-block;
            min-width: 56px;
            padding: 10px 14px;
            margin-right: 8px;
            text-align: center;
            border-radius: 8px;
            background: #eef2ff;
            font-weight: 700;
            font-size: 1.05rem;
            border: 1px solid #c7d2fe;
            white-space: nowrap;
            word-break: normal;
            vertical-align: middle;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()


def ensure_schema():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS test_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            score INTEGER,
            time_taken_seconds INTEGER DEFAULT 0,
            date TIMESTAMP DEFAULT (datetime('now','localtime'))
        )
        """
    )
    cursor.execute("PRAGMA table_info(test_history)")
    history_columns = [column[1] for column in cursor.fetchall()]
    if "time_taken_seconds" not in history_columns:
        cursor.execute("ALTER TABLE test_history ADD COLUMN time_taken_seconds INTEGER DEFAULT 0")
    conn.commit()


def format_duration(total_seconds):
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def get_history(username):
    cursor.execute(
        "SELECT score,time_taken_seconds,date FROM test_history WHERE username=? ORDER BY id ASC",
        (username,),
    )
    return cursor.fetchall()


def get_marking_rules(mode):
    if mode == "Practice":
        return {
            "mcq_correct": 1.0,
            "mcq_wrong": 0.0,
            "memory_max": 1.0,
        }
    return {
        "mcq_correct": 1.0,
        "mcq_wrong": -0.25,
        "memory_max": 1.0,
    }


def start_test(mode):
    st.session_state.questions = generate_test()
    st.session_state.answers = {}
    st.session_state.score = None
    st.session_state.test_submitted = False
    st.session_state.test_start_time = time.time()
    st.session_state.auto_submitted = False
    st.session_state.time_taken_seconds = 0
    st.session_state.current_question_idx = 0
    st.session_state.visited_questions = []
    st.session_state.submit_confirmation_text = ""
    st.session_state.attempted_questions = 0
    st.session_state.submission_saved = False
    st.session_state.review_rows = []
    st.session_state.max_score = 0.0
    st.session_state.score_breakdown = {"positive": 0.0, "negative": 0.0, "partial": 0.0}
    st.session_state.tab_switch_violations = 0
    st.session_state.test_mode = mode
    st.session_state.test_duration_seconds = 25 * 60 if mode == "Exam" else 45 * 60


def build_review_sheet_text(review_rows):
    lines = [
        "Cognitive Assessment Review Sheet",
        f"Mode: {st.session_state.test_mode}",
        f"Score: {st.session_state.score:.2f}/{st.session_state.max_score:.2f}",
        f"Time Taken: {format_duration(st.session_state.time_taken_seconds)}",
        f"Tab Switch Violations: {st.session_state.tab_switch_violations}",
        "",
    ]

    for row in review_rows:
        lines.extend(
            [
                f"Question {row['question_no']}: {row['question_type']}",
                f"Prompt: {row['prompt']}",
                f"Your Answer: {row['user_answer']}",
                f"Correct Answer: {row['correct_answer']}",
                f"Marks: {row['marks']:.2f}",
                f"Result: {row['result']}",
                "",
            ]
        )

    return "\n".join(lines)


def sync_tab_switch_violations_from_query():
    try:
        raw_value = st.query_params.get("violations", "0")
        if isinstance(raw_value, list):
            raw_value = raw_value[0] if raw_value else "0"
        parsed = int(str(raw_value))
        st.session_state.tab_switch_violations = max(st.session_state.tab_switch_violations, parsed)
    except (ValueError, TypeError):
        pass


def submit_test():
    rules = get_marking_rules(st.session_state.test_mode)
    score = 0.0
    attempted_questions = 0
    positive_marks = 0.0
    negative_marks = 0.0
    partial_marks = 0.0
    review_rows = []

    def token_list(raw_text):
        return [item.strip().lower() for item in raw_text.split() if item.strip()]

    def overlap_fraction(correct_items, user_items):
        if not correct_items:
            return 0.0
        correct_set = set(correct_items)
        user_set = set(user_items)
        return len(correct_set.intersection(user_set)) / len(correct_set)

    def add_review_row(index, question_type, prompt, user_answer, correct_answer, marks, result):
        review_rows.append(
            {
                "question_no": index + 1,
                "question_type": question_type,
                "prompt": prompt,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "marks": round(marks, 2),
                "result": result,
            }
        )

    for i, q in enumerate(st.session_state.questions):
        marks = 0.0
        result = "Unattempted"

        # -------- MCQ --------
        if "options" in q:
            user_answer = st.session_state.answers.get(i)
            correct_answer = q.get("answer")

            if user_answer is not None:
                attempted_questions += 1
                if correct_answer is None:
                    marks = 0.0
                    result = "Attempted (No key)"
                elif _is_mcq_answer_correct(q, user_answer, correct_answer):
                    marks = rules["mcq_correct"]
                    result = "Correct"
                else:
                    marks = rules["mcq_wrong"]
                    result = "Wrong"

            if marks > 0:
                positive_marks += marks
            elif marks < 0:
                negative_marks += marks
            score += marks

            add_review_row(
                i,
                "MCQ",
                q.get("question", "MCQ"),
                str(user_answer) if user_answer is not None else "Not Attempted",
                str(correct_answer) if correct_answer is not None else "Not Provided",
                marks,
                result,
            )

        # -------- TEXT RESPONSE --------
        elif q.get("input_type") == "text":
            user_answer = st.session_state.answers.get(i)
            correct_answer = q.get("answer")

            if user_answer is not None and str(user_answer).strip():
                attempted_questions += 1
                if correct_answer is None:
                    marks = 0.0
                    result = "Attempted (No key)"
                elif _normalize_answer_token(user_answer) == _normalize_answer_token(correct_answer):
                    marks = rules["mcq_correct"]
                    result = "Correct"
                else:
                    marks = rules["mcq_wrong"]
                    result = "Wrong"

            if marks > 0:
                positive_marks += marks
            elif marks < 0:
                negative_marks += marks
            score += marks

            add_review_row(
                i,
                "Text Response",
                q.get("question", "Text Response"),
                str(user_answer) if user_answer is not None else "Not Attempted",
                str(correct_answer) if correct_answer is not None else "Not Provided",
                marks,
                result,
            )

        # -------- WORD MEMORY --------
        elif q.get("type") == "word_memory":
            user_raw = st.session_state.get(f"user_answer_{i}", "").strip()
            correct_words = [item.lower() for item in st.session_state.get(f"memory_words_{i}", [])]
            user_words = token_list(user_raw)

            if user_raw:
                attempted_questions += 1
                marks = rules["memory_max"] * overlap_fraction(correct_words, user_words)
                if marks >= 0.99:
                    result = "Correct"
                elif marks > 0:
                    result = "Partially Correct"
                else:
                    result = "Wrong"

            score += marks
            if marks > 0:
                if marks < 0.99:
                    partial_marks += marks
                else:
                    positive_marks += marks

            add_review_row(
                i,
                "Word Memory",
                "Recall the shown words in any order",
                user_raw if user_raw else "Not Attempted",
                " ".join(correct_words),
                marks,
                result,
            )

        # -------- NUMBER MEMORY --------
        elif q.get("type") == "number_memory":
            user_raw = st.session_state.get(f"user_answer_{i}", "").strip()
            correct_text = "".join(map(str, st.session_state.get(f"numbers_{i}", [])))

            if user_raw:
                attempted_questions += 1
                aligned = list(zip(correct_text, user_raw))
                matched = sum(1 for a, b in aligned if a == b)
                marks = rules["memory_max"] * (matched / len(correct_text)) if correct_text else 0.0
                if marks >= 0.99:
                    result = "Correct"
                elif marks > 0:
                    result = "Partially Correct"
                else:
                    result = "Wrong"

            score += marks
            if marks > 0:
                if marks < 0.99:
                    partial_marks += marks
                else:
                    positive_marks += marks

            add_review_row(
                i,
                "Number Memory",
                "Recall the number sequence in exact order",
                user_raw if user_raw else "Not Attempted",
                correct_text,
                marks,
                result,
            )


        # -------- IMAGE MEMORY --------
        elif q.get("type") == "image_memory":
            user_raw = st.session_state.get(f"user_answer_{i}", "").strip()
            correct_images = [item.lower() for item in st.session_state.get(f"shown_images_{i}", [])]
            user_images = token_list(user_raw)

            if user_raw:
                attempted_questions += 1
                marks = rules["memory_max"] * overlap_fraction(correct_images, user_images)
                if marks >= 0.99:
                    result = "Correct"
                elif marks > 0:
                    result = "Partially Correct"
                else:
                    result = "Wrong"

            score += marks
            if marks > 0:
                if marks < 0.99:
                    partial_marks += marks
                else:
                    positive_marks += marks

            add_review_row(
                i,
                "Image Memory",
                "Recall the shown image labels",
                user_raw if user_raw else "Not Attempted",
                " ".join(correct_images),
                marks,
                result,
            )


        # -------- GRID MEMORY --------
        elif q.get("type") == "grid_memory":
            user = st.session_state.get(f"user_answer_{i}", [])
            correct_cells = set(st.session_state.get(f"grid_pattern_{i}", []))
            if len(user) > 0:
                attempted_questions += 1
                matched = len(correct_cells.intersection(set(user)))
                marks = rules["memory_max"] * (matched / len(correct_cells)) if correct_cells else 0.0
                if marks >= 0.99:
                    result = "Correct"
                elif marks > 0:
                    result = "Partially Correct"
                else:
                    result = "Wrong"

            score += marks
            if marks > 0:
                if marks < 0.99:
                    partial_marks += marks
                else:
                    positive_marks += marks

            add_review_row(
                i,
                "Grid Memory",
                "Recall highlighted grid positions",
                " ".join(map(str, user)) if user else "Not Attempted",
                " ".join(map(str, sorted(correct_cells))),
                marks,
                result,
            )


        # -------- NBACK / IMAGE ORDER MEMORY --------
        elif q.get("type") == "nback":
            user_raw = st.session_state.get(f"user_answer_{i}", "").strip()
            correct_seq = [item.lower() for item in st.session_state.get(f"nback_images_{i}", [])]
            user_seq = token_list(user_raw)

            if user_raw:
                attempted_questions += 1
                marks = rules["memory_max"] * overlap_fraction(correct_seq, user_seq)
                if marks >= 0.99:
                    result = "Correct"
                elif marks > 0:
                    result = "Partially Correct"
                else:
                    result = "Wrong"

            score += marks
            if marks > 0:
                if marks < 0.99:
                    partial_marks += marks
                else:
                    positive_marks += marks

            add_review_row(
                i,
                "Image Sequence Memory",
                "Recall image sequence",
                user_raw if user_raw else "Not Attempted",
                " ".join(correct_seq),
                marks,
                result,
            )

    st.session_state.score = round(score, 2)
    st.session_state.max_score = round(float(len(st.session_state.questions)), 2)
    st.session_state.attempted_questions = attempted_questions
    st.session_state.review_rows = review_rows
    st.session_state.score_breakdown = {
        "positive": round(positive_marks, 2),
        "negative": round(negative_marks, 2),
        "partial": round(partial_marks, 2),
    }

    if st.session_state.test_start_time is not None:
        st.session_state.time_taken_seconds = int(time.time() - st.session_state.test_start_time)
    else:
        st.session_state.time_taken_seconds = 0

    st.session_state.test_submitted = True


def save_submission(username):
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO test_history(username,score,time_taken_seconds,date) VALUES (?,?,?,?)",
        (username, st.session_state.score, st.session_state.time_taken_seconds, submitted_at),
    )
    conn.commit()


def reset_test_state():
    st.session_state.questions = None
    st.session_state.answers = {}
    st.session_state.score = None
    st.session_state.test_submitted = False
    st.session_state.test_start_time = None
    st.session_state.auto_submitted = False
    st.session_state.time_taken_seconds = 0
    st.session_state.current_question_idx = 0
    st.session_state.visited_questions = []
    st.session_state.attempted_questions = 0
    st.session_state.submission_saved = False
    st.session_state.review_rows = []
    st.session_state.max_score = 0.0
    st.session_state.score_breakdown = {"positive": 0.0, "negative": 0.0, "partial": 0.0}
    st.session_state.tab_switch_violations = 0


def is_test_active():
    return (
        st.session_state.logged_in
        and st.session_state.questions is not None
        and not st.session_state.test_submitted
    )


def render_palette_styles(total_questions):
    visited_questions = set(st.session_state.visited_questions)
    answered_questions = {
        idx for idx, answer in st.session_state.answers.items() if answer is not None
    }
    style_lines = ["<style>"]

    for idx in range(total_questions):
        selector = f'.st-key-jump_{idx} button'
        if idx in answered_questions:
            background = "#2563eb"
            border = "#2563eb"
            color = "#ffffff"
        elif idx in visited_questions:
            background = "#dc2626"
            border = "#dc2626"
            color = "#ffffff"
        else:
            background = "#d1d5db"
            border = "#d1d5db"
            color = "#111827"

        style_lines.append(
            f"{selector} {{background-color: {background} !important; border-color: {border} !important; color: {color} !important;}}"
        )

    style_lines.append("</style>")
    st.markdown("".join(style_lines), unsafe_allow_html=True)


def render_header():
    st.markdown('<div class="app-header"><h3 style="margin:0;">Cognitive Assessment System</h3></div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 2, 1])

    if col1.button("Home", use_container_width=True):
        st.session_state.current_page = "home"
    if col2.button("Signup", use_container_width=True):
        st.session_state.current_page = "signup"
    if col3.button("Login", use_container_width=True, key="nav_login"):
        st.session_state.current_page = "login"
    if col4.button("Resources", use_container_width=True):
        st.session_state.current_page = "resources"

    if st.session_state.logged_in:
        col5.markdown(f"<div style='text-align:right;padding-top:8px;'>Logged in: <b>{st.session_state.username}</b></div>", unsafe_allow_html=True)
        if col6.button("Logout", use_container_width=True):
            reset_test_state()
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.current_page = "home"
            st.rerun()


def build_sample_questions_pdf():
    lines = [
        "Cognitive Assessment - Sample Question Paper",
        "Duration: 25 minutes | Total Questions: 20",
        "",
        "Section A: Logical Reasoning",
        "1. Find the next number: 3, 8, 15, 24, 35, ?",
        "2. Statement: All coders are problem-solvers.",
        "   Conclusion: Some problem-solvers are coders.",
        "",
        "Section B: Quantitative Aptitude",
        "3. Solve: (27 x 4) - (56 / 7)",
        "4. If 12 workers finish a task in 15 days,",
        "   how many days for 18 workers?",
        "",
        "Section C: Verbal Ability",
        "5. Choose synonym for 'resilient'.",
        "6. Rearrange: quickly / solved / she / puzzle / the",
        "",
        "Section D: Memory",
        "7. Memorize and reproduce: 9 4 1 7 2 8",
        "8. Recall sequence: river lamp cloud tiger",
        "",
        "Rule: Attempt all questions in sequence and track time.",
    ]

    def _escape_pdf_text(text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    text_stream_lines = [
        "BT",
        "/F1 12 Tf",
        "72 765 Td",
        "16 TL",
    ]
    for line in lines:
        text_stream_lines.append(f"({_escape_pdf_text(line)}) Tj")
        text_stream_lines.append("T*")
    text_stream_lines.append("ET")

    stream = "\n".join(text_stream_lines)
    stream_bytes = stream.encode("latin-1", errors="replace")

    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream",
    ]

    pdf = "%PDF-1.4\n"
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf.encode("latin-1")))
        pdf += f"{idx} 0 obj\n{obj}\nendobj\n"

    xref_start = len(pdf.encode("latin-1"))
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n"

    pdf += (
        "trailer\n"
        f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_start}\n"
        "%%EOF"
    )

    return pdf.encode("latin-1", errors="replace")


def render_resources_page():
    st.subheader("Improvement Resources")
    st.caption("Use this section to build exam readiness with materials, practice papers, and a structured daily routine.")

    st.markdown(
        """
        <style>
        .resource-domain-card {
            background: linear-gradient(165deg, #edf6ff 0%, #dcecff 100%);
            border: 1px solid #b8d2ee;
            border-radius: 14px;
            padding: 14px;
            min-height: 160px;
            box-shadow: 0 8px 20px rgba(15, 60, 105, 0.08);
            margin-bottom: 10px;
        }
        .resource-domain-title {
            color: #0f2e4f;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .resource-domain-sub {
            color: #2d537a;
            font-size: 0.92rem;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Domain Material Cards")
    card1, card2, card3, card4 = st.columns(4)
    with card1:
        st.markdown(
            """
            <div class="resource-domain-card">
                <div class="resource-domain-title">Logical Reasoning</div>
                <div class="resource-domain-sub">Series, coding-decoding, blood relations, statement-conclusion practice sets with timer drills.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card2:
        st.markdown(
            """
            <div class="resource-domain-card">
                <div class="resource-domain-title">Quantitative Aptitude</div>
                <div class="resource-domain-sub">Percentages, ratio-proportion, averages, speed maths and data interpretation focused modules.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card3:
        st.markdown(
            """
            <div class="resource-domain-card">
                <div class="resource-domain-title">Verbal Ability</div>
                <div class="resource-domain-sub">Vocabulary, sentence arrangement, comprehension and grammar correction micro tests.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card4:
        st.markdown(
            """
            <div class="resource-domain-card">
                <div class="resource-domain-title">Memory & Focus</div>
                <div class="resource-domain-sub">Number recall, word recall, image sequence and concentration strengthening sessions.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if "resource_mock_questions" not in st.session_state:
        st.session_state.resource_mock_questions = []

    if "resource_focus_mode" not in st.session_state:
        st.session_state.resource_focus_mode = "Balanced"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Study Tracks")
        st.selectbox(
            "Select your focus track",
            ["Balanced", "Speed", "Accuracy", "Memory", "Reasoning"],
            key="resource_focus_mode",
        )
        track_map = {
            "Balanced": [
                "20 min quantitative drills",
                "20 min verbal reasoning",
                "20 min memory training",
            ],
            "Speed": [
                "15 min rapid arithmetic",
                "15 min pattern puzzles with timer",
                "30 min mini mock with strict timing",
            ],
            "Accuracy": [
                "25 min untimed logical sets",
                "20 min error analysis review",
                "15 min correction notebook",
            ],
            "Memory": [
                "15 min number recall",
                "15 min word sequence recall",
                "30 min image/grid recall practice",
            ],
            "Reasoning": [
                "20 min syllogism + assumptions",
                "20 min sequence + coding",
                "20 min mixed reasoning quiz",
            ],
        }
        st.markdown("**Recommended Daily Plan**")
        for item in track_map[st.session_state.resource_focus_mode]:
            st.write(f"- {item}")

    with c2:
        st.markdown("### Quick Actions")
        if st.button("Generate 10-Question Practice Sheet", use_container_width=True):
            generated = generate_test()
            st.session_state.resource_mock_questions = generated[:10]

        if st.button("Start Full Mock Test (25 mins)", type="primary", use_container_width=True):
            start_test("Exam")
            st.session_state.current_page = "login"
            st.rerun()

    st.markdown("### Downloadable Material")

    with (PROJECT_ROOT / "data" / "questions.json").open("r", encoding="utf-8") as qf:
        question_bank_json = qf.read()

    st.download_button(
        label="Download Question Bank (JSON)",
        data=question_bank_json,
        file_name="cognitive_question_bank.json",
        mime="application/json",
        use_container_width=True,
    )

    sample_pdf = build_sample_questions_pdf()
    st.download_button(
        label="Download Sample Question Paper (PDF)",
        data=sample_pdf,
        file_name="sample_question_paper.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    sample_sheet_lines = [
        "Cognitive Assessment Practice Sheet",
        "",
        "Section 1: Logical Reasoning",
        "1. Identify the next item in the sequence: 2, 6, 12, 20, ?",
        "2. If all A are B and some B are C, what can be concluded?",
        "",
        "Section 2: Quantitative",
        "3. Solve under 45 seconds: (18 * 7) - (64 / 8)",
        "4. Ratio puzzle: If x:y = 3:5 and y:z = 10:7, find x:z",
        "",
        "Section 3: Verbal",
        "5. Choose the closest synonym of 'meticulous'",
        "6. Rearrangement: Arrange the sentence fragments into meaningful order",
        "",
        "Section 4: Memory",
        "7. Memorize and reproduce: 4 1 9 7 3 8",
        "8. Memorize and reproduce in order: apple lamp cloud tiger",
        "",
        "Review Rule:",
        "- Mark every wrong answer with reason: concept, speed, or misread.",
        "- Retake same sheet after 48 hours.",
    ]
    practice_sheet_text = "\n".join(sample_sheet_lines)

    st.download_button(
        label="Download Practice Paper (TXT)",
        data=practice_sheet_text,
        file_name="practice_paper_01.txt",
        mime="text/plain",
        use_container_width=True,
    )

    if st.session_state.resource_mock_questions:
        st.markdown("### Generated Practice Sheet (10 Questions)")
        for idx, q in enumerate(st.session_state.resource_mock_questions, 1):
            if "question" in q:
                st.markdown(f"**{idx}. {q['question']}**")
                if "options" in q:
                    for opt in q["options"]:
                        st.write(f"- {opt}")
            elif q.get("type"):
                st.markdown(f"**{idx}. Memory Task: {q['type'].replace('_', ' ').title()}**")

    st.markdown("### Weekly Improvement Targets")
    target_col1, target_col2, target_col3 = st.columns(3)
    target_col1.metric("Mock Tests / Week", "4")
    target_col2.metric("Accuracy Target", "85%+")
    target_col3.metric("Avg Completion", "< 22:00")

    st.info("Tip: After every test, review mistakes in the History page and repeat only weak sections the next day.")


def render_home_page():
    st.markdown('<div class="home-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-kicker">Timed Cognitive Assessment Platform</div>
            <div class="hero-title">Evaluate focus, logic, and performance in a real exam-style environment.</div>
            <div class="hero-copy">
                Cognitive Assessment System is a professional web-based testing platform built to measure
                reasoning ability, concentration, and response accuracy through timed assessments. It combines
                a structured examination workflow with score tracking, attempt history, and performance insights
                so users can understand both their current level and their improvement over time.
            </div>
            <div class="hero-tags">
                <div class="hero-tag">25 Minute Timed Test</div>
                <div class="hero-tag">Auto Submission</div>
                <div class="hero-tag">Performance Tracking</div>
                <div class="hero-tag">Exam Style Interface</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card_col1, card_col2, card_col3 = st.columns(3, gap="large")
    with card_col1:
        st.markdown(
            """
            <div class="feature-card card-delay-1">
                <div class="feature-icon">01</div>
                <div class="feature-title">Real-Time Test Flow</div>
                <div class="feature-copy">
                    Launch a timed assessment, answer inside a focused exam interface, and let the system manage
                    countdown, navigation, and automatic submission at timeout.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_col2:
        st.markdown(
            """
            <div class="feature-card card-delay-2">
                <div class="feature-icon">02</div>
                <div class="feature-title">Meaningful Performance Tracking</div>
                <div class="feature-copy">
                    Every attempt records score, duration, and exact completion time, making it easier to review
                    consistency, identify gaps, and measure improvement across sessions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_col3:
        st.markdown(
            """
            <div class="feature-card card-delay-3">
                <div class="feature-icon">03</div>
                <div class="feature-title">Purpose-Driven Assessment</div>
                <div class="feature-copy">
                    The platform is designed to simulate a practical online examination system while helping users
                    build confidence, monitor progress, and practice under real time pressure.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    info_col1, info_col2 = st.columns(2, gap="large")
    with info_col1:
        st.markdown(
            """
            <div class="section-panel card-delay-4">
                <h4>What This Website Offers</h4>
                <p>A clean exam workflow, 25-minute timed assessments, automatic submission, instant scoring,
                detailed history, and visual progress tracking for repeat users.</p>
                <h4>Purpose Of The Project</h4>
                <p>To build a structured cognitive testing environment that feels realistic, remains easy to use,
                and helps users evaluate thinking performance in a measurable way.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with info_col2:
        st.markdown(
            """
            <div class="section-panel card-delay-5">
                <h4>How It Works</h4>
                <p>Sign up or log in, generate a test, answer questions inside the exam interface, submit manually
                with confirmation or let the timer auto-submit, then review your results and historical progress.</p>
                <h4>Main Goal</h4>
                <p>To help users understand their reasoning speed, accuracy, and consistency while creating a strong,
                professional experience for online assessment practice.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not st.session_state.logged_in:
        st.warning("Login to generate test and view your history analytics.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    username = st.session_state.username

    st.markdown("### Test Setup")
    st.radio(
        "Select Mode",
        ["Exam", "Practice"],
        key="home_test_mode",
        horizontal=True,
    )

    action_col1, action_col2 = st.columns(2)

    if action_col1.button("Generate Test", type="primary", use_container_width=True):
        start_test(st.session_state.home_test_mode)
        st.session_state.current_page = "login"
        st.rerun()

    if action_col2.button("History", use_container_width=True):
        st.session_state.current_page = "history"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_history_page():
    st.subheader("Performance History")

    if not st.session_state.logged_in:
        st.warning("Login to view your score graph and attempt details.")
        return

    username = st.session_state.username
    history = get_history(username)

    if not history:
        st.info("No test records yet. Complete a test to see analytics.")
        return

    scores = [row[0] for row in history]
    times = [row[1] if row[1] is not None else 0 for row in history]
    attempts = list(range(1, len(history) + 1))

    current_score = scores[-1]
    first_score = scores[0]
    improvement = current_score - first_score
    avg_time = int(sum(times) / len(times))

    m1, m2, m3 = st.columns(3)
    m1.metric("Latest Score", current_score)
    m2.metric("Improvement", improvement)
    m3.metric("Avg Time", format_duration(avg_time))

    chart_df = pd.DataFrame(
        {
            "Attempt": attempts,
            "Score": scores,
            "Time Taken (sec)": times,
        }
    )

    score_chart = (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Attempt:Q", axis=alt.Axis(title="Attempt", tickMinStep=1)),
            y=alt.Y("Score:Q", axis=alt.Axis(title="Score"), scale=alt.Scale(domainMin=0)),
            tooltip=["Attempt", "Score"],
        )
        .properties(height=300)
    )
    st.altair_chart(score_chart, use_container_width=True)

    attempt_rows = [
        {
            "Attempt": idx + 1,
            "Score": row[0],
            "Time Taken": format_duration(row[1] if row[1] is not None else 0),
            "Date & Time": row[2],
        }
        for idx, row in enumerate(history)
    ]
    st.subheader("Attempt Details")
    st.table(attempt_rows)


def render_signup_page():
    st.subheader("Create Account")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Signup"):
        if create_user(username, password):
            st.success("Account created successfully. You can now login.")
            st.session_state.current_page = "login"
        else:
            st.error("Username already exists")


def render_exam_page(username):
    if st.session_state.get("_exam_rendered_this_run", False):
        return
    st.session_state._exam_rendered_this_run = True

    st.markdown('<div class="exam-title">Real-Time Examination</div>', unsafe_allow_html=True)
    sync_tab_switch_violations_from_query()
    rules = get_marking_rules(st.session_state.test_mode)
    if st.session_state.test_mode == "Exam":
        st.caption("Exam Mode: strict monitoring, negative marking, and auto-submit at 00:00.")
    else:
        st.caption("Practice Mode: no negative marking and proctoring disabled.")

    if st.session_state.test_start_time is None:
        st.session_state.test_start_time = time.time()

    elapsed_seconds = int(time.time() - st.session_state.test_start_time)
    remaining_seconds = max(0, st.session_state.test_duration_seconds - elapsed_seconds)

    def is_answered(idx, q):
        if "options" in q:
            return st.session_state.answers.get(idx) is not None
        if q.get("type") in {"word_memory", "number_memory", "image_memory", "nback"}:
            return st.session_state.get(f"user_answer_{idx}", "") != ""
        if q.get("type") == "grid_memory":
            return len(st.session_state.get(f"user_answer_{idx}", [])) > 0
        return False

    answered_count = sum(
        1 for idx, q in enumerate(st.session_state.questions) if is_answered(idx, q)
    )
    total_questions = len(st.session_state.questions)

    if st.session_state.test_submitted:
        if st.session_state.test_mode == "Exam":
            render_proctor_component(False, strict_mode=True)

        if st.session_state.auto_submitted:
            st.warning("Time limit reached. Test was automatically submitted.")

        if not st.session_state.submission_saved:
            save_submission(username)
            st.session_state.submission_saved = True

        st.subheader("Test Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score", f"{st.session_state.score:.2f}/{st.session_state.max_score:.2f}")
        m2.metric("Questions Answered", st.session_state.attempted_questions)
        m3.metric("Time Taken", format_duration(st.session_state.time_taken_seconds))
        m4.metric("Tab Switch Violations", st.session_state.tab_switch_violations)

        b1, b2, b3 = st.columns(3)
        b1.metric("Positive Marks", st.session_state.score_breakdown.get("positive", 0.0))
        b2.metric("Partial Marks", st.session_state.score_breakdown.get("partial", 0.0))
        b3.metric("Negative Marks", st.session_state.score_breakdown.get("negative", 0.0))

        st.info(
            f"Marking Rules: +{rules['mcq_correct']} correct | {rules['mcq_wrong']} wrong MCQ | up to {rules['memory_max']} partial marks on memory tasks"
        )

        review_text = build_review_sheet_text(st.session_state.review_rows)
        review_df = pd.DataFrame(st.session_state.review_rows)
        review_csv = review_df.to_csv(index=False) if not review_df.empty else ""

        d1, d2 = st.columns(2)
        d1.download_button(
            "Download Review Sheet (TXT)",
            data=review_text,
            file_name="test_review_sheet.txt",
            mime="text/plain",
            use_container_width=True,
        )
        d2.download_button(
            "Download Review Sheet (CSV)",
            data=review_csv,
            file_name="test_review_sheet.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if st.button("GO BACK", use_container_width=True):
            reset_test_state()
            st.session_state.current_page = "home"
            st.rerun()

        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Time Remaining", format_duration(remaining_seconds))
    c2.metric("Answered", f"{answered_count}/{total_questions}")
    c3.metric("Questions", total_questions)

    if st.session_state.test_mode == "Exam":
        proctor_left, proctor_right = st.columns([3, 1])
        with proctor_right:
            render_proctor_component(True, strict_mode=True)

    progress = answered_count / total_questions if total_questions else 0
    st.progress(progress, text=f"Progress: {answered_count}/{total_questions} answered")

    left_col, right_col = st.columns([5, 1])

    current_idx = st.session_state.current_question_idx
    if current_idx >= total_questions:
        current_idx = total_questions - 1
    if current_idx < 0:
        current_idx = 0
    st.session_state.current_question_idx = current_idx
    if current_idx not in st.session_state.visited_questions:
        st.session_state.visited_questions.append(current_idx)

    render_palette_styles(total_questions)

    with left_col:
        st.markdown('<div class="exam-shell">', unsafe_allow_html=True)
        question = st.session_state.questions[current_idx]
        st.markdown(f"**Question {current_idx + 1} of {total_questions}**")

        if question.get("passage"):
            st.info(question["passage"])

        image_path = _resolve_question_image_path(question.get("image"))
        if image_path is not None:
            st.image(str(image_path), use_container_width=True)

        if "options" in question:
            option_items = _build_option_items(question["options"])
            option_labels = [item["label"] for item in option_items]
            current_answer = st.session_state.answers.get(current_idx)
            default_index = None
            for idx, item in enumerate(option_items):
                if _normalize_answer_token(current_answer) in {
                    _normalize_answer_token(item["value"]),
                    _normalize_answer_token(item["key"]),
                    _normalize_answer_token(item["label"]),
                }:
                    default_index = idx
                    break

            st.markdown(f"<div class='question-text'>{question['question']}</div>", unsafe_allow_html=True)

            # If any option is an image, render image tiles with select buttons
            if any(item["image_path"] is not None for item in option_items):
                cols_per_row = 2 if len(option_items) > 2 else len(option_items)
                for i in range(0, len(option_items), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx >= len(option_items):
                            continue
                        item = option_items[idx]
                        with cols[j]:
                            # show a smaller image preview
                            if item["image_path"] is not None:
                                st.image(str(item["image_path"]), width=140)
                            else:
                                st.write(item["value"])

                            # selection button shown as a circle to mimic radio
                            selected_now = _normalize_answer_token(st.session_state.answers.get(current_idx)) in {
                                _normalize_answer_token(item["value"]),
                                _normalize_answer_token(item["key"]),
                            }
                            circle = "◉" if selected_now else "◯"
                            label = f"{circle} {item['key']}"
                            if st.button(label, key=f"select_{current_idx}_{item['key']}"):
                                st.session_state.answers[current_idx] = item["value"]

                            # visually mark selection with a subtle success box
                            if selected_now:
                                st.markdown("<div style='background:#e6ffed;padding:8px;border-radius:6px;margin-top:6px;'>Selected</div>", unsafe_allow_html=True)
            else:
                selected_label = st.radio(
                    "Select one option:",
                    option_labels,
                    key=f"answer_{current_idx}",
                    index=default_index,
                )

                selected_item = next(
                    (item for item in option_items if item["label"] == selected_label),
                    None,
                )
                st.session_state.answers[current_idx] = selected_item["value"] if selected_item else None

        elif question.get("input_type") == "text":
            st.markdown(f"<div class='question-text'>{question.get('question', 'Text Question')}</div>", unsafe_allow_html=True)
            answer = st.text_input(
                "Enter your answer:",
                key=f"text_answer_{current_idx}",
            )
            st.session_state.answers[current_idx] = answer if answer.strip() else None

        elif question.get("type") == "number_memory":
            st.markdown("<div class='question-text'>Number Memory</div>", unsafe_allow_html=True)
            number_memory_test(current_idx)
            st.session_state.answers[current_idx] = st.session_state.get(f"user_answer_{current_idx}", None)

        elif question.get("type") == "word_memory":
            st.markdown("<div class='question-text'>Word Memory</div>", unsafe_allow_html=True)
            word_memory_test(current_idx)
            st.session_state.answers[current_idx] = st.session_state.get(f"user_answer_{current_idx}", None)

        elif question.get("type") == "image_memory":
            st.markdown("<div class='question-text'>Image Memory</div>", unsafe_allow_html=True)
            image_memory_test(current_idx)
            st.session_state.answers[current_idx] = st.session_state.get(f"user_answer_{current_idx}", None)

        elif question.get("type") == "nback":
            st.markdown("<div class='question-text'>Image Sequence Memory</div>", unsafe_allow_html=True)
            nback_memory_test(current_idx)
            st.session_state.answers[current_idx] = st.session_state.get(f"user_answer_{current_idx}", None)

        elif question.get("type") == "grid_memory":
            st.markdown("<div class='question-text'>Grid Memory</div>", unsafe_allow_html=True)
            grid_memory_test(current_idx)
            st.session_state.answers[current_idx] = st.session_state.get(f"user_answer_{current_idx}", None)

        else:
            st.session_state.answers[current_idx] = None

        memory_display_active = any(
            st.session_state.get(f"{flag}_{current_idx}", False)
            for flag in ["show_numbers", "show_words", "show_images", "show_grid", "show_nback"]
        )

        if not memory_display_active:
            st.text_input(
                "Type submit to confirm final submission",
                key="submit_confirmation_text",
                placeholder="submit",
            )

            nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])
            if nav_col1.button("Previous", use_container_width=True, disabled=current_idx == 0):
                st.session_state.current_question_idx = current_idx - 1
                st.rerun()
            if nav_col2.button("Next", use_container_width=True, disabled=current_idx == total_questions - 1):
                st.session_state.current_question_idx = current_idx + 1
                st.rerun()
            if nav_col3.button(
                "Submit Test",
                type="primary",
                use_container_width=True,
                key="submit_test_main",
                disabled=st.session_state.submit_confirmation_text.strip().lower() != "submit",
            ):
                st.session_state.auto_submitted = False
                submit_test()
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="palette-title">Question Palette</div>', unsafe_allow_html=True)
        st.caption("Blue = Answered | Red = Unattempted | Gray = Unvisited")

        palette_cols = st.columns(4)
        for idx in range(total_questions):
            button_label = str(idx + 1)
            col = palette_cols[idx % 4]
            if col.button(button_label, key=f"jump_{idx}", use_container_width=True):
                st.session_state.current_question_idx = idx
                st.rerun()

    if (
        st.session_state.test_mode == "Exam"
        and not st.session_state.test_submitted
        and remaining_seconds == 0
    ):
        st.session_state.auto_submitted = True
        submit_test()
        st.rerun()

    if not st.session_state.test_submitted and remaining_seconds > 0:
        return

def render_login_page():
    if not st.session_state.logged_in:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", type="primary", key="login_submit"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid login")
        return

    username = st.session_state.username

    st.subheader("Candidate Dashboard")
    st.write("Start your test below. Once started, you will enter exam mode.")

    st.radio(
        "Select Mode",
        ["Exam", "Practice"],
        key="login_test_mode",
        horizontal=True,
    )

    if st.button("Generate Test", type="primary"):
        start_test(st.session_state.login_test_mode)
        st.rerun()

    cursor.execute(
        "SELECT score,time_taken_seconds,date FROM test_history WHERE username=? ORDER BY id DESC",
        (username,),
    )
    history = cursor.fetchall()

    st.subheader("Previous Test History")
    if history:
        history_rows = [
            {
                "Score": row[0],
                "Time Taken": format_duration(row[1] if row[1] is not None else 0),
                "Date": row[2],
            }
            for row in history
        ]
        st.table(history_rows)
    else:
        st.write("No previous history found.")


init_state()
ensure_schema()
apply_theme()
render_header()
st.session_state._exam_rendered_this_run = False

if st.session_state.logged_in and st.session_state.questions is not None:
    render_exam_page(st.session_state.username)
    st.stop()

if st.session_state.current_page == "home":
    render_home_page()
elif st.session_state.current_page == "signup":
    render_signup_page()
elif st.session_state.current_page == "history":
    render_history_page()
elif st.session_state.current_page == "resources":
    render_resources_page()
else:
    render_login_page()
