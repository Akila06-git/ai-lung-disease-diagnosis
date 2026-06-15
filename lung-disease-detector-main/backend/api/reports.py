"""
PDF Medical Report Generator for the Lung Disease Detector.

Generates professional hospital-style diagnostic reports using ReportLab.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage,
    HRFlowable,
)

logger = logging.getLogger(__name__)


def generate_medical_report(prediction) -> io.BytesIO:
    """Generate a PDF medical report for a given Prediction instance.

    Args:
        prediction: A Prediction model instance with all fields populated.

    Returns:
        A BytesIO object containing the PDF report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0ea5e9"),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyText2",
        parent=styles["BodyText"],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=14,
    )
    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
        leading=10,
    )

    elements = []

    # ── Header ──
    elements.append(Paragraph("🫁 AI Lung Disease Diagnostic Report", title_style))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        small_style,
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor("#e2e8f0"),
        spaceAfter=10, spaceBefore=6,
    ))

    # ── Patient Information ──
    elements.append(Paragraph("Patient Information", heading_style))
    patient_data = [
        ["Name:", prediction.patient_name or "N/A"],
        ["Age:", str(prediction.patient_age) if prediction.patient_age else "N/A"],
        ["Sex:", {"M": "Male", "F": "Female", "O": "Other"}.get(prediction.patient_sex or "", "N/A")],
        ["Scan Date:", prediction.created_at.strftime("%B %d, %Y") if prediction.created_at else "N/A"],
        ["Report ID:", f"#LDD-{prediction.id:05d}"],
    ]
    patient_table = Table(patient_data, colWidths=[100, 350])
    patient_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1e293b")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(patient_table)

    # ── X-Ray Image ──
    if prediction.image:
        try:
            elements.append(Paragraph("X-Ray Image", heading_style))
            img_path = prediction.image.path
            elements.append(RLImage(img_path, width=3 * inch, height=3 * inch, kind="proportional"))
            elements.append(Spacer(1, 6))
        except Exception as e:
            logger.warning("Could not embed X-ray image in report: %s", e)

    # ── Heatmap Image (if available) ──
    if hasattr(prediction, "heatmap_image") and prediction.heatmap_image:
        try:
            elements.append(Paragraph("AI Attention Heatmap (Grad-CAM)", heading_style))
            heatmap_path = prediction.heatmap_image.path
            elements.append(RLImage(heatmap_path, width=3 * inch, height=3 * inch, kind="proportional"))
            elements.append(Spacer(1, 6))
        except Exception as e:
            logger.warning("Could not embed heatmap image in report: %s", e)

    # ── AI Diagnosis ──
    elements.append(Paragraph("AI Diagnosis Results", heading_style))
    confidence_pct = round(prediction.confidence_score * 100, 1)
    diagnosis_data = [
        ["Predicted Condition:", prediction.predicted_class],
        ["Confidence:", f"{confidence_pct}%"],
        ["Urgency Level:", prediction.urgency_level.replace("_", " ")],
        ["Processing Time:", f"{prediction.processing_time_ms:.0f} ms"],
    ]
    diag_table = Table(diagnosis_data, colWidths=[140, 310])
    diag_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1e293b")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(diag_table)

    # ── Immediate Actions ──
    if prediction.immediate_actions:
        elements.append(Paragraph("Immediate Actions", heading_style))
        for action in prediction.immediate_actions:
            elements.append(Paragraph(f"• {action}", body_style))

    # ── Medical Recommendations ──
    if prediction.medical_recommendations:
        elements.append(Paragraph("Medical Recommendations", heading_style))
        for rec in prediction.medical_recommendations:
            elements.append(Paragraph(f"• {rec}", body_style))

    # ── Lifestyle Recommendations ──
    if prediction.lifestyle_recommendations:
        elements.append(Paragraph("Lifestyle Recommendations", heading_style))
        for rec in prediction.lifestyle_recommendations:
            elements.append(Paragraph(f"• {rec}", body_style))

    # ── Follow-Up ──
    if prediction.follow_up:
        elements.append(Paragraph("Follow-Up Guidance", heading_style))
        elements.append(Paragraph(prediction.follow_up, body_style))

    # ── Symptoms ──
    if prediction.symptoms:
        elements.append(Paragraph("Reported Symptoms", heading_style))
        elements.append(Paragraph(prediction.symptoms, body_style))

    # ── Disclaimer ──
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"),
        spaceAfter=6, spaceBefore=6,
    ))
    elements.append(Paragraph(
        f"⚠️ {prediction.disclaimer}",
        small_style,
    ))
    elements.append(Paragraph(
        "This report was generated by the AI Lung Disease Detector system. "
        "It is intended for screening purposes only and must not replace "
        "professional medical diagnosis. Always consult a qualified healthcare provider.",
        small_style,
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    logger.info("PDF report generated for prediction #%s", prediction.id)
    return buffer
