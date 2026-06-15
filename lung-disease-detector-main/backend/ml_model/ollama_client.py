"""
Ollama LLM client for generating detailed medical advice.

Communicates with a local Ollama instance via its REST API to produce
multi-paragraph, clinically relevant symptom analyses.

Configuration via environment variables:
    OLLAMA_BASE_URL   – default http://localhost:11434
    OLLAMA_MODEL      – default tinyllama  (change to llama3, medllama2, etc.)
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import os
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — reads from Django settings when available, else env / defaults
# ---------------------------------------------------------------------------


def _get_setting(name: str, default: str) -> str:
    """Read from Django settings if configured, otherwise from env or default."""
    try:
        from django.conf import settings as django_settings
        return str(getattr(django_settings, name, None) or os.environ.get(name, default))
    except Exception:
        return os.environ.get(name, default)


OLLAMA_BASE_URL: str = _get_setting("OLLAMA_BASE_URL", "http://localhost:11434")

# Logic to switch between models based on env var or settings
_use_medllama = _get_setting("USE_MEDLLAMA", "False").lower() == "true"
_default_model = "medllama2" if _use_medllama else "tinyllama"
OLLAMA_MODEL: str = _get_setting("OLLAMA_MODEL", _default_model)

OLLAMA_TIMEOUT: int = int(_get_setting("OLLAMA_TIMEOUT", "120"))


# ---------------------------------------------------------------------------
# System prompt – instructs the LLM to act as a medical advisor
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a medical AI assistant. "
    "Your task is to review a Chest X-ray diagnosis and patient reported symptoms. "
    "Provide a concise analysis and actionable advice.\n\n"
    "Please structure your response as follows:\n"
    "1. Analysis: Explain the diagnosis and validation/contradiction of symptoms.\n"
    "2. Recommendations: List 3 key medical or lifestyle steps.\n"
    "3. When to see a doctor: List critical warning signs.\n\n"
    "Keep the language simple and direct. Do not make up patient questions."
)


def generate_medical_advice(
    disease: str,
    symptoms: str,
    patient_age: Optional[int] = None,
    patient_sex: Optional[str] = None,
    language: str = "English",
) -> Optional[str]:
    """
    Call the local Ollama API to generate detailed medical advice.

    Returns the generated text as a string, or None on failure.
    """
    if not symptoms or not symptoms.strip():
        return None

    # Build a rich, contextual prompt
    patient_info = ""
    if patient_age:
        patient_info += f"Age: {patient_age}. "
    if patient_sex:
        sex_map = {"M": "Male", "F": "Female", "O": "Other"}
        patient_info += f"Sex: {sex_map.get(patient_sex, patient_sex)}. "

    user_prompt = (
        f"Diagnosis: {disease}\n"
        f"Patient Info: {patient_info or 'None'}\n"
        f"Symptoms: {symptoms}\n\n"
        f"Please provide a medical analysis based on the above.\n"
        f"CRITICAL INSTRUCTION: You MUST write your ENTIRE response in {language}."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": user_prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 500,       # ~500 tokens for a detailed response
            "repeat_penalty": 1.15,
        },
    }

    url = f"{OLLAMA_BASE_URL}/api/generate"

    try:
        logger.info(
            "Calling Ollama (%s) for disease=%s, symptoms=%s",
            OLLAMA_MODEL, disease, symptoms[:50],
        )
        resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        advice = data.get("response", "").strip()

        if not advice:
            logger.warning("Ollama returned empty response for prediction.")
            return None

        logger.info("Ollama advice generated (%d chars): %s...", len(advice), advice[:120])
        return advice

    except requests.exceptions.ConnectionError:
        logger.error(
            "Cannot connect to Ollama at %s. Is the Ollama service running? "
            "Start it with: ollama serve",
            OLLAMA_BASE_URL,
        )
        return None
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out after %ds.", OLLAMA_TIMEOUT)
        return None
    except Exception as e:
        logger.error("Ollama API error: %s", e)
        return None
