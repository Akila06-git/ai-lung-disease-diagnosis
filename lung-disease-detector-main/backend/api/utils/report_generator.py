from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def generate_pdf_report(prediction: Any) -> bytes:
    """Generate a simple medical-style PDF report for a prediction.

    Returns the PDF bytes which can be sent to the frontend for download.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    styles = getSampleStyleSheet()

    margin = 20 * mm
    y = height - margin

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, "Lung Disease Screening Report")
    y -= 15 * mm

    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Report ID: {prediction.id}")
    y -= 5 * mm
    c.drawString(margin, y, f"Generated at: {datetime.utcnow().isoformat()} UTC")
    y -= 10 * mm

    # Prediction summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Prediction Summary")
    y -= 7 * mm

    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Predicted Class: {prediction.predicted_class}")
    y -= 5 * mm
    c.drawString(margin, y, f"Confidence: {prediction.confidence_percentage:.2f}%")
    y -= 5 * mm
    c.drawString(margin, y, f"Urgency Level: {prediction.urgency_level}")
    y -= 10 * mm

    # Recommendations
    def _draw_list(title: str, items: list[str], y_pos: float) -> float:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y_pos, title)
        y_pos -= 6 * mm
        c.setFont("Helvetica", 10)
        for item in items:
            c.drawString(margin + 5 * mm, y_pos, f"- {item}")
            y_pos -= 5 * mm
        return y_pos - 4 * mm

    y = _draw_list("Immediate Actions", prediction.immediate_actions, y)
    y = _draw_list("Medical Recommendations", prediction.medical_recommendations, y)
    y = _draw_list("Lifestyle Recommendations", prediction.lifestyle_recommendations, y)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Follow-up")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, prediction.follow_up)
    y -= 10 * mm

    # Disclaimer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margin, y, prediction.disclaimer)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

