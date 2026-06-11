"""
HuggingFace Inference API service — ClimateHealth AI.

Uses the free serverless Inference API (no local model download).
Model: facebook/bart-large-mnli  — zero-shot text classification.

Used for:
  - Disease signal detection in news / social-media text
  - Symptom-to-disease classification

Note: HF free tier cold-starts can take 20-30s on first request.
      Subsequent calls are fast. A 503 with "loading" means retry in ~20s.
"""
import httpx
from app.core.config import settings

_HF_BASE       = "https://api-inference.huggingface.co/models"
_CLASSIFIER    = "facebook/bart-large-mnli"

_SIGNAL_LABELS = [
    "malaria outbreak",
    "influenza epidemic",
    "cholera contamination",
    "disease spreading",
    "health emergency",
    "no disease risk",
]

_SYMPTOM_LABELS = [
    "malaria",
    "influenza",
    "cholera",
    "pneumonia",
    "dengue fever",
    "typhoid fever",
]


def _headers() -> dict:
    if not settings.HUGGINGFACE_API_KEY:
        raise RuntimeError("HUGGINGFACE_API_KEY is not configured.")
    return {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}


async def _zero_shot(text: str, labels: list[str]) -> dict:
    """Call the HuggingFace zero-shot classification endpoint."""
    url     = f"{_HF_BASE}/{_CLASSIFIER}"
    payload = {"inputs": text, "parameters": {"candidate_labels": labels}}

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(url, headers=_headers(), json=payload)

        # HF returns 503 with {"error":"loading"} on cold start — surface clearly
        if resp.status_code == 503:
            detail = resp.json().get("error", "Model is loading")
            raise RuntimeError(f"HuggingFace model unavailable: {detail}. Retry in ~20s.")

        resp.raise_for_status()

    data = resp.json()
    return {
        "labels": data["labels"],
        "scores": [round(float(s), 3) for s in data["scores"]],
    }


async def detect_disease_signal(text: str) -> dict:
    """
    Classify free text (news article, social media post, field report) for
    disease outbreak signals. Returns ranked labels with confidence scores.

    Example input:
      "Many residents report mosquito infestations after recent flooding."
    Example output:
      { "top_signal": "malaria outbreak", "confidence": 0.91, ... }
    """
    result = await _zero_shot(text[:1000], _SIGNAL_LABELS)
    return {
        "top_signal":  result["labels"][0],
        "confidence":  result["scores"][0],
        "all_scores":  dict(zip(result["labels"], result["scores"])),
        "input_text":  text[:200],
        "model":       _CLASSIFIER,
    }


async def classify_symptoms(symptoms: str) -> dict:
    """
    Map a free-text symptom description to a ranked list of likely diseases.

    Example input:  "I have fever, chills, sweating and severe headache."
    Example output: { "most_likely": "malaria", "confidence": 0.87, ... }
    """
    result = await _zero_shot(symptoms[:500], _SYMPTOM_LABELS)
    return {
        "most_likely_disease": result["labels"][0],
        "confidence":          result["scores"][0],
        "differential":        dict(zip(result["labels"][:4], result["scores"][:4])),
        "symptoms_input":      symptoms[:200],
        "model":               _CLASSIFIER,
    }
