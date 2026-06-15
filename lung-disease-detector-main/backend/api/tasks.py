from __future__ import annotations

import logging
from datetime import timedelta
from time import perf_counter

from celery import shared_task
from django.utils import timezone

from .models import Prediction
from .serializers import PredictionSerializer
from .validators import validate_xray_image
from ml_model.recommendations import get_disease_recommendations

logger = logging.getLogger(__name__)

# IMPORTANT: This order MUST match the alphabetical directory order used by
# ImageDataGenerator.flow_from_directory() during training on Kaggle.
CLASS_NAMES = [
    "Normal", "Edema", "Pneumothorax",
    "Pneumonia-Bacterial", "Pneumonia-Viral", "COVID-19",
    "Tuberculosis", "Emphysema"
]


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def predict_image_task(self, prediction_id: int, language: str = "English") -> int:
    """Celery task to run ML prediction on a stored image.

    Returns the ID of the updated Prediction instance.
    """
    try:
        # Import heavy ML dependencies lazily inside the worker process.
        from ml_model.predict import predict_image
        from ml_model.biobert import analyze_symptoms
        prediction = Prediction.objects.get(id=prediction_id)
    except Prediction.DoesNotExist as exc:  # pragma: no cover - defensive
        logger.error("Prediction object not found: %s", exc)
        raise

    image_path = prediction.image.path
    start = perf_counter()

    try:
        # Validate again at worker side as a defense-in-depth measure
        with open(image_path, "rb") as f:
            validate_xray_image(f, prediction.image.name)

        predicted_class, confidence, model_time_ms = predict_image(
            image_path=image_path,
            class_names=CLASS_NAMES,
        )
        recs = get_disease_recommendations(predicted_class)

        # Apply Ollama-powered symptom analysis if symptoms provided
        if prediction.symptoms:
             try:
                 bio_recs = analyze_symptoms(
                     predicted_class,
                     prediction.symptoms,
                     patient_age=prediction.patient_age,
                     patient_sex=prediction.patient_sex,
                     language=language,
                 )
                 advice = bio_recs.get("biobert_advice")
                 if advice:
                     # Prepend AI advice to immediate actions
                     recs["immediate_actions"].insert(0, f"[AI Suggestion]: {advice}")
                     logger.info("AI advice added for prediction %s (%d chars)", prediction.id, len(advice))
                 else:
                     logger.warning("AI analysis returned no advice for prediction %s", prediction.id)
             except Exception as e:
                 logger.error("AI symptom analysis failed: %s", e)

        total_time_ms = (perf_counter() - start) * 1000.0

        prediction.predicted_class = predicted_class
        prediction.confidence_score = confidence
        prediction.urgency_level = recs["urgency_level"]
        prediction.urgency_color = recs["urgency_color"]
        prediction.urgency_icon = recs["urgency_icon"]
        prediction.immediate_actions = recs["immediate_actions"]
        prediction.medical_recommendations = recs["medical_recommendations"]
        prediction.lifestyle_recommendations = recs["lifestyle_recommendations"]
        prediction.follow_up = recs["follow_up"]
        prediction.disclaimer = recs["disclaimer"]
        prediction.processing_time_ms = total_time_ms
        prediction.cached_result = False
        prediction.save(update_fields=[
            "predicted_class",
            "confidence_score",
            "urgency_level",
            "urgency_color",
            "urgency_icon",
            "immediate_actions",
            "medical_recommendations",
            "lifestyle_recommendations",
            "follow_up",
            "disclaimer",
            "processing_time_ms",
            "cached_result",
        ])

        # Generate Grad-CAM heatmap overlay
        try:
            from ml_model.interpretability import create_gradcam_overlay
            class_index = CLASS_NAMES.index(predicted_class)
            heatmap_buffer = create_gradcam_overlay(image_path, class_index)
            
            from django.core.files.base import ContentFile
            heatmap_filename = f"gradcam_{prediction.id}.jpg"
            prediction.heatmap_image.save(
                heatmap_filename,
                ContentFile(heatmap_buffer.read()),
                save=True,
            )
            logger.info("Grad-CAM heatmap saved for prediction %s", prediction.id)
        except Exception as e:
            logger.warning("Grad-CAM generation failed (non-fatal): %s", e)

        logger.info(
            "Prediction %s completed: %s (%.2f%%) in %.2f ms",
            prediction.id,
            prediction.predicted_class,
            prediction.confidence_percentage,
            total_time_ms,
        )
        return prediction.id
    except Exception as exc:  # pragma: no cover - Celery handles retries
        try:
            countdown = 2 ** self.request.retries
        except Exception:
            countdown = 10
        logger.error("Error during prediction task: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task
def cleanup_old_predictions(days: int = 30) -> int:
    """Periodic task to delete predictions older than a given number of days.

    Returns the count of deleted records.
    """
    threshold = timezone.now() - timedelta(days=days)
    qs = Prediction.objects.filter(created_at__lt=threshold)
    count = qs.count()
    qs.delete()
    logger.info("Deleted %s old predictions (older than %s days)", count, days)
    return count


# ---------------------------------------------------------------------------
# Model Retraining Tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=0)
def retrain_model_task(self) -> dict:
    """Celery task to retrain the model using corrected predictions.

    Can be triggered manually from Django Admin or via API.
    Returns a dict with training results.
    """
    logger.info("Retrain task started (task_id=%s)", self.request.id)

    try:
        from ml_model.retrain import retrain_model
        result = retrain_model()

        if result["status"] == "success":
            # Reload the model in the worker process
            from ml_model.predict import reload_model
            reload_model()
            logger.info("Model reloaded after successful retraining.")

        logger.info("Retrain task completed: %s", result)
        return result

    except Exception as exc:
        logger.error("Retrain task failed: %s", exc, exc_info=True)
        return {"status": "error", "message": str(exc)}


@shared_task
def scheduled_retrain_task() -> dict:
    """Periodic Celery task for monthly retraining.

    Should be added to CELERY_BEAT_SCHEDULE in settings.py.
    Only runs if there are enough corrected samples.
    """
    logger.info("Scheduled monthly retraining triggered.")

    from api.models import Prediction
    corrected_count = Prediction.objects.filter(
        is_corrected=True,
        true_class__isnull=False,
    ).count()

    if corrected_count < 5:
        msg = f"Skipping scheduled retrain: only {corrected_count} corrected samples (need 5+)."
        logger.info(msg)
        return {"status": "skipped", "message": msg}

    # Delegate to the main retrain task
    return retrain_model_task.apply().result
