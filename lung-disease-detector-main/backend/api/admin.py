from django.contrib import admin, messages
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "predicted_class",
        "confidence_percentage",
        "true_class",
        "is_corrected",
        "patient_name",
        "created_at",
    )
    list_filter = (
        "predicted_class",
        "is_corrected",
        "urgency_level",
        "created_at",
    )
    search_fields = ("patient_name", "predicted_class", "true_class")
    readonly_fields = ("image_hash", "processing_time_ms", "cached_result", "created_at")
    list_editable = ("true_class", "is_corrected")

    actions = ["trigger_retrain"]

    @admin.action(description="🔁 Retrain model using corrected predictions")
    def trigger_retrain(self, request, queryset):
        """Admin action to trigger model retraining via Celery."""
        from .tasks import retrain_model_task

        # Count available corrected predictions (not just selected)
        corrected_count = Prediction.objects.filter(
            is_corrected=True,
            true_class__isnull=False,
        ).count()

        if corrected_count < 2:
            self.message_user(
                request,
                f"Not enough corrected predictions ({corrected_count}). "
                f"Need at least 2 to retrain.",
                messages.WARNING,
            )
            return

        task = retrain_model_task.delay()
        self.message_user(
            request,
            f"🚀 Retraining task queued (task_id: {task.id}). "
            f"Using {corrected_count} corrected predictions. "
            f"Check Celery logs or Flower for progress.",
            messages.SUCCESS,
        )
