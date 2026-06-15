from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


def prediction_image_upload_path(instance: "Prediction", filename: str) -> str:
    """Generate a safe upload path for prediction images.

    The original filename is discarded to avoid path traversal issues; we only
    keep the extension.
    """
    import uuid
    from pathlib import Path

    ext = Path(filename).suffix.lower() or ".jpg"
    return f"xray_images/{uuid.uuid4().hex}{ext}"


class UserProfile(models.Model):
    """Stores extended user information like role."""
    
    class Role(models.TextChoices):
        DOCTOR = "DOCTOR", "Doctor"
        PATIENT = "PATIENT", "Patient"
        
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
        help_text="The RBAC role of the user."
    )
    
    def __str__(self):
        return f"{self.user.username} Profile ({self.role})"


class Prediction(models.Model):
    """Stores a single prediction result for an uploaded chest X-ray."""

    class DiseaseClass(models.TextChoices):
        NORMAL = "Normal", "Normal"
        EDEMA = "Edema", "Edema"
        PNEUMOTHORAX = "Pneumothorax", "Pneumothorax"
        PNEUMONIA_BACTERIAL = "Pneumonia-Bacterial", "Pneumonia-Bacterial"
        PNEUMONIA_VIRAL = "Pneumonia-Viral", "Pneumonia-Viral"
        COVID19 = "COVID-19", "COVID-19"
        TUBERCULOSIS = "Tuberculosis", "Tuberculosis"
        EMPHYSEMA = "Emphysema", "Emphysema"
        UNKNOWN = "Unknown", "Unknown"

    class UrgencyLevel(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM_HIGH = "MEDIUM_HIGH", "Medium-High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    image = models.ImageField(
        upload_to=prediction_image_upload_path,
        help_text="Uploaded chest X-ray image.",
    )
    image_hash = models.CharField(
        max_length=64,
        unique=False,
        db_index=True,
        help_text="SHA-256 hash of the image bytes for cache lookups.",
    )

    predicted_class = models.CharField(
        max_length=64,
        choices=DiseaseClass.choices,
        default=DiseaseClass.UNKNOWN,
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model confidence in the prediction (0-1).",
    )

    urgency_level = models.CharField(
        max_length=32,
        choices=UrgencyLevel.choices,
    )
    urgency_color = models.CharField(
        max_length=16,
        help_text="Tailwind-compatible color name for frontend badges.",
    )
    urgency_icon = models.CharField(
        max_length=8,
        help_text="Unicode icon representing urgency.",
    )

    immediate_actions = models.JSONField(
        default=list,
        help_text="Immediate actions to take for this disease.",
    )
    medical_recommendations = models.JSONField(
        default=list,
        help_text="Medical recommendations and interventions.",
    )
    lifestyle_recommendations = models.JSONField(
        default=list,
        help_text="Lifestyle changes to support recovery.",
    )
    follow_up = models.TextField(
        help_text="Follow-up guidance and typical timelines.",
    )
    disclaimer = models.TextField(
        default=(
            "This is an AI-assisted screening tool. Not a medical diagnosis. "
            "Consult a healthcare provider."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processing_time_ms = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="End-to-end processing time in milliseconds.",
    )
    cached_result = models.BooleanField(
        default=False,
        help_text="Whether this prediction was served from cache.",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="predictions",
        help_text="User who uploaded this image.",
    )

    patient_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Patient's full name.",
    )
    patient_age = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Patient's age in years.",
    )
    patient_sex = models.CharField(
        max_length=1,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        null=True,
        blank=True,
        help_text="Patient's biological sex.",
    )
    
    symptoms = models.TextField(
        null=True,
        blank=True,
        help_text="Patient reported symptoms for BioBERT analysis.",
    )
    
    heatmap_image = models.ImageField(
        upload_to="heatmaps/",
        null=True,
        blank=True,
        help_text="Grad-CAM heatmap overlay image.",
    )

    # --- Feedback / Active-learning fields ---
    true_class = models.CharField(
        max_length=64,
        choices=DiseaseClass.choices,
        null=True,
        blank=True,
        help_text="Correct class label provided by user feedback.",
    )
    is_corrected = models.BooleanField(
        default=False,
        help_text="Whether a user has submitted a correction for this prediction.",
    )
    corrected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the correction was submitted.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["image_hash"], name="idx_image_hash"),
            models.Index(fields=["predicted_class"], name="idx_predicted_class"),
            models.Index(fields=["created_at"], name="idx_created_at"),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.predicted_class} ({self.confidence_score:.2%})"

    @property
    def confidence_percentage(self) -> float:
        """Return confidence as a 0-100 percentage."""
        return float(self.confidence_score * 100.0)

