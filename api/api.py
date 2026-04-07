"""
TruthSeeker — Local Misinformation Detection API
Powered by FastAPI + scikit-learn
"""

import os
import re
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ─── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger("truthseeker")

# ─── Paths ──────────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent
MODEL_PATH     = BASE_DIR / "models" / "truthseeker_model.joblib"
VECTORIZER_PATH = BASE_DIR / "models" / "truthseeker_vectorizer.joblib"

# ─── Global model refs (populated at startup) ──────────────
model = None
vectorizer = None


# ─── Lifespan (load model once) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML artifacts before the server starts accepting requests."""
    global model, vectorizer

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}\n"
            "Place truthseeker_model.joblib in the api/models/ directory."
        )
    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(
            f"Vectorizer file not found: {VECTORIZER_PATH}\n"
            "Place truthseeker_vectorizer.joblib in the api/models/ directory."
        )

    log.info("Loading model from %s", MODEL_PATH)
    model = joblib.load(MODEL_PATH)
    log.info("Loading vectorizer from %s", VECTORIZER_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    log.info("✅  Model and vectorizer loaded successfully.")

    yield  # ← app runs here

    log.info("Shutting down — releasing model resources.")
    model = None
    vectorizer = None


# ─── App ────────────────────────────────────────────────────
app = FastAPI(
    title="TruthSeeker API",
    description="Real-time misinformation detection powered by ML.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Chrome extension (and localhost dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                # Chrome extensions use chrome-extension:// origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Raw text to analyze for truthfulness.",
        examples=["Scientists confirm that vaccines are safe and effective."],
    )


class AnalyzeResponse(BaseModel):
    text_snippet: str = Field(description="First 200 chars of the submitted text.")
    classification: str = Field(description="'Real' or 'Fake'.")
    truth_score: float = Field(description="Confidence score as percentage (0-100).")
    label: int = Field(description="1 = Real, 0 = Fake.")


# ─── Text preprocessing (mirrors training) ─────────────────
def clean_text(text: str) -> str:
    """Apply the same cleaning pipeline used during training."""
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ─── Endpoints ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "model_loaded": model is not None,
        "service": "TruthSeeker Misinformation Detector",
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_text(payload: AnalyzeRequest):
    """
    Analyze a piece of text and return a truthfulness score.
    """
    if model is None or vectorizer is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Restart the server.",
        )

    cleaned = clean_text(payload.text)
    if not cleaned:
        raise HTTPException(
            status_code=422,
            detail="Text is empty after cleaning. Provide meaningful content.",
        )

    # Vectorize
    features = vectorizer.transform([cleaned])

    # Predict
    prediction = model.predict(features)[0]

    # Confidence via decision function (linear classifier)
    decision = model.decision_function(features)[0]
    # Sigmoid-ish mapping to 0-100 %
    confidence = float(1 / (1 + np.exp(-decision))) * 100

    classification = "Real" if prediction == 1 else "Fake"

    log.info(
        "Analyzed %d chars → %s (%.1f%%)",
        len(payload.text),
        classification,
        confidence,
    )

    return AnalyzeResponse(
        text_snippet=payload.text[:200],
        classification=classification,
        truth_score=round(confidence, 2),
        label=int(prediction),
    )
