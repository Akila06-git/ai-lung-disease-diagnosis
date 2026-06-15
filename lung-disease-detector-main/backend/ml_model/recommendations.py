from __future__ import annotations

from typing import Dict, Any


DISCLAIMER_TEXT = (
    "This is an AI-assisted screening tool. Not a medical diagnosis. "
    "Consult a healthcare provider."
)


DISEASE_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "COVID-19": {
        "urgency_level": "HIGH",
        "urgency_color": "red",
        "urgency_icon": "🚨",
        "immediate_actions": [
            "Isolate from others immediately.",
            "Call emergency services if experiencing breathing difficulty.",
            "Inform recent contacts about possible exposure.",
        ],
        "medical_recommendations": [
            "Schedule a telehealth consultation within 24 hours.",
            "Monitor oxygen saturation regularly if possible.",
            "Discuss eligibility for antiviral medications with a clinician.",
        ],
        "lifestyle_recommendations": [
            "Use prone positioning (lying on your stomach) to ease breathing.",
            "Maintain adequate hydration and nutrition.",
            "Use a separate bathroom if available and disinfect surfaces regularly.",
        ],
        "follow_up": "Repeat chest X-ray in 2–4 weeks or sooner if symptoms worsen.",
    },
    "Tuberculosis": {
        "urgency_level": "HIGH",
        "urgency_color": "red",
        "urgency_icon": "🚨",
        "immediate_actions": [
            "Arrange an urgent appointment with a pulmonologist.",
            "Wear a mask to reduce airborne transmission risk.",
            "Encourage close contacts to undergo TB screening.",
        ],
        "medical_recommendations": [
            "Begin a full 6–9 month course of appropriate antibiotics.",
            "Consider directly observed therapy (DOT) to ensure adherence.",
            "Obtain sputum culture and sensitivity testing.",
        ],
        "lifestyle_recommendations": [
            "Practice cough etiquette (cover mouth and dispose of tissues safely).",
            "Ensure adequate rest and follow a high-nutrition diet.",
        ],
        "follow_up": "Monthly sputum tests and regular clinical follow-up as advised.",
    },
    "Bacterial Pneumonia": {
        "urgency_level": "MEDIUM_HIGH",
        "urgency_color": "orange",
        "urgency_icon": "🟠",
        "immediate_actions": [
            "Consult a physician promptly to evaluate severity.",
            "Start prescribed antibiotics as soon as they are available.",
        ],
        "medical_recommendations": [
            "Complete the entire course of prescribed antibiotics.",
            "Use antipyretics for fever control if recommended by a clinician.",
        ],
        "lifestyle_recommendations": [
            "Prioritize rest and avoid strenuous activity.",
            "Maintain hydration and avoid smoking or secondhand smoke.",
        ],
        "follow_up": "Repeat chest X-ray in 4–6 weeks to confirm resolution.",
    },
    "Viral Pneumonia": {
        "urgency_level": "MEDIUM",
        "urgency_color": "yellow",
        "urgency_icon": "🟡",
        "immediate_actions": [
            "Monitor for worsening breathing, chest pain, or confusion.",
            "Use symptom-relief medications as directed by a clinician.",
        ],
        "medical_recommendations": [
            "Discuss antiviral options if indicated for the specific virus.",
            "Focus on supportive care such as oxygen or fluids if required.",
        ],
        "lifestyle_recommendations": [
            "Rest adequately and avoid overexertion.",
            "Maintain hydration and consider over-the-counter fever reducers if appropriate.",
        ],
        "follow_up": "Arrange clinical reassessment in 1–2 weeks or sooner if symptoms worsen.",
    },
    "Normal": {
        "urgency_level": "LOW",
        "urgency_color": "green",
        "urgency_icon": "🟢",
        "immediate_actions": [
            "No emergency intervention appears necessary based on this image.",
        ],
        "medical_recommendations": [
            "Continue with routine medical check-ups as scheduled.",
        ],
        "lifestyle_recommendations": [
            "Maintain a healthy lifestyle including exercise, balanced diet, and avoiding smoking.",
        ],
        "follow_up": "Consider annual screening if you have risk factors for lung disease.",
    },
}


def get_disease_recommendations(disease_name: str) -> Dict[str, Any]:
    """Return structured recommendations for a given disease name."""
    default = {
        "urgency_level": "MEDIUM",
        "urgency_color": "yellow",
        "urgency_icon": "🟡",
        "immediate_actions": [
            "Consult a healthcare provider to discuss these findings.",
        ],
        "medical_recommendations": [
            "Additional imaging or tests may be required.",
        ],
        "lifestyle_recommendations": [
            "Maintain healthy habits and monitor for new symptoms.",
        ],
        "follow_up": "Follow the schedule recommended by your clinician.",
    }
    import copy
    data = copy.deepcopy(DISEASE_RECOMMENDATIONS.get(disease_name, default))
    data["disclaimer"] = DISCLAIMER_TEXT
    return data

