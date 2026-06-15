"""
Symptom analysis module — powered by Ollama LLM.

This module provides the ``analyze_symptoms`` function that is called by the
Celery prediction task. It delegates to a local Ollama instance for rich,
multi-paragraph medical advice.

Falls back to a sensible default message when Ollama is unavailable.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def analyze_symptoms(
    disease: str,
    symptoms: str,
    patient_age: int | None = None,
    patient_sex: str | None = None,
    language: str = "English",
) -> dict:
    """
    Generate detailed medical advice using Ollama LLM.

    Returns a dict with key ``biobert_advice`` containing the generated text,
    or an empty dict on failure / missing input.

    The key name ``biobert_advice`` is kept for backward compatibility with
    the frontend and task code.
    """
    if not symptoms or not symptoms.strip():
        return {}

    try:
        from ml_model.ollama_client import generate_medical_advice

        advice = generate_medical_advice(
            disease=disease,
            symptoms=symptoms,
            patient_age=patient_age,
            patient_sex=patient_sex,
            language=language,
        )

        if advice:
            logger.info("Ollama advice generated (%d chars)", len(advice))
            return {"biobert_advice": advice}
        else:
            logger.warning("Ollama returned no advice; using fallback.")
            return _fallback_advice(disease, symptoms)

    except Exception as e:
        logger.error("Ollama analysis failed: %s", e)
        return _fallback_advice(disease, symptoms)


def _fallback_advice(disease: str, symptoms: str) -> dict:
    """Provide a basic fallback when Ollama is unavailable."""
    fallback = (
        f"Based on your reported symptoms ({symptoms}) and the screening result "
        f"({disease}), we recommend consulting a healthcare provider for a "
        f"thorough evaluation. While this AI screening tool provides initial "
        f"assessments, a qualified medical professional can offer personalized "
        f"diagnosis and treatment options tailored to your specific condition.\n\n"
        f"If you experience worsening symptoms such as difficulty breathing, "
        f"persistent high fever, or chest pain, please seek immediate medical "
        f"attention."
    )
    return {"biobert_advice": fallback}
