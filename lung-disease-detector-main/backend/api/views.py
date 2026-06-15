

from __future__ import annotations

import logging

from celery.result import AsyncResult
from django.db.models import Q
from django.http import Http404
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Prediction
from .serializers import PredictionSerializer, RegisterSerializer
from .utils.hash_utils import generate_image_hash
from .validators import validate_xray_image
from ml_model.recommendations import get_disease_recommendations
from .analytics import get_dashboard_stats


logger = logging.getLogger(__name__)


class PredictView(APIView):
    """Handle image upload and dispatch async prediction task."""

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Import here to avoid heavy ML imports during Django startup
        from .tasks import predict_image_task
        file_obj = request.FILES.get("image")
        if not file_obj:
            return Response(
                {"detail": "No image file provided under 'image' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run validations
        try:
            validate_xray_image(file_obj, file_obj.name)
        except Exception as exc:
            logger.warning("Image validation failed: %s", exc)
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # DICOM conversion: convert .dcm files to PNG before processing
        dicom_metadata = {}
        from ml_model.dicom_utils import is_dicom_file
        if is_dicom_file(file_obj.name):
            try:
                from ml_model.dicom_utils import convert_dicom_to_image
                from django.core.files.uploadedfile import InMemoryUploadedFile
                png_buffer, dicom_metadata = convert_dicom_to_image(file_obj)
                # Replace the file object with the converted PNG
                file_obj = InMemoryUploadedFile(
                    file=png_buffer,
                    field_name="image",
                    name=file_obj.name.rsplit(".", 1)[0] + ".png",
                    content_type="image/png",
                    size=png_buffer.getbuffer().nbytes,
                    charset=None,
                )
                logger.info("DICOM file converted to PNG, metadata: %s", dicom_metadata)
            except Exception as exc:
                logger.error("DICOM conversion failed: %s", exc)
                return Response(
                    {"detail": f"Failed to process DICOM file: {exc}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            # Hash-based caching
            image_hash = generate_image_hash(file_obj)
            
            from django.conf import settings
            should_cache = getattr(settings, "ENABLE_IMAGE_CACHING", True)
            
            cached = None
            if should_cache:
                cached = Prediction.objects.filter(image_hash=image_hash).first()

            # Extract patient details & symptoms from request (needed for both cached and new)
            symptoms = request.data.get("symptoms", "") or ""
            patient_name = request.data.get("patient_name", "") or ""
            patient_age = request.data.get("patient_age")
            patient_sex = request.data.get("patient_sex", "") or ""

            # Convert age safely
            try:
                patient_age = int(patient_age) if patient_age else None
            except (ValueError, TypeError):
                patient_age = None
            
            # Auto-fill from DICOM metadata if user didn't provide values
            if dicom_metadata:
                if not patient_name and dicom_metadata.get("patient_name"):
                    patient_name = dicom_metadata["patient_name"]
                if not patient_age and dicom_metadata.get("patient_age"):
                    patient_age = dicom_metadata["patient_age"]
                if not patient_sex and dicom_metadata.get("patient_sex"):
                    patient_sex = dicom_metadata["patient_sex"]
            
            language = request.data.get("language", "English") or "English"

            if cached:
                # If symptoms provided, run BioBERT analysis inline on the cached result
                if symptoms.strip():
                    from ml_model.biobert import analyze_symptoms
                    cached.symptoms = symptoms
                    cached.patient_name = patient_name or cached.patient_name
                    cached.patient_age = patient_age or cached.patient_age
                    cached.patient_sex = patient_sex or cached.patient_sex

                    try:
                        bio_recs = analyze_symptoms(cached.predicted_class, symptoms, language=language)
                        advice = bio_recs.get("biobert_advice")
                        if advice:
                            # Prepend AI advice to existing recommendations
                            actions = list(cached.immediate_actions or [])
                            # Remove old AI suggestions
                            actions = [a for a in actions if not a.startswith("[AI Suggestion]")]
                            actions.insert(0, f"[AI Suggestion]: {advice}")
                            cached.immediate_actions = actions

                            med_recs = list(cached.medical_recommendations or [])
                            med_recs = [r for r in med_recs if not r.startswith("Based on symptoms")]
                            med_recs.append(f"Based on symptoms '{symptoms}': {advice}")
                            cached.medical_recommendations = med_recs
                    except Exception as e:
                        logger.error("BioBERT analysis failed on cached result: %s", e)

                    cached.save(update_fields=[
                        "symptoms", "patient_name", "patient_age", "patient_sex",
                        "immediate_actions", "medical_recommendations",
                    ])

                serializer = PredictionSerializer(cached, context={"request": request})
                return Response(
                    {
                        "status": "completed",
                        "cached": True,
                        "prediction": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            # No cache hit: create prediction stub and enqueue async task
            user = request.user if request.user.is_authenticated else None
            logger.info("PredictView: User=%s (Auth=%s)", request.user, request.user.is_authenticated)

            prediction = Prediction.objects.create(
                image=file_obj,
                image_hash=image_hash,
                user=user,
                patient_name=patient_name,
                patient_age=patient_age,
                patient_sex=patient_sex,
                symptoms=symptoms,
                predicted_class=Prediction.DiseaseClass.UNKNOWN,
                confidence_score=0.0,
                urgency_level="MEDIUM",
                urgency_color="yellow",
                urgency_icon="🟡",
                immediate_actions=[],
                medical_recommendations=[],
                lifestyle_recommendations=[],
                follow_up="Pending model evaluation.",
                disclaimer=(
                    "This is an AI-assisted screening tool. Not a medical diagnosis. "
                    "Consult a healthcare provider."
                ),
                processing_time_ms=0.0,
                cached_result=False,
            )

            task = predict_image_task.delay(prediction.id, language=language)
            logger.info("Enqueued prediction task %s for prediction %s, language %s", task.id, prediction.id, language)

            return Response(
                {
                    "task_id": task.id,
                    "status": "processing",
                    "cached": False,
                    "prediction_id": prediction.id,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            import traceback
            logger.error("Error processing prediction request: %s\n%s", e, traceback.format_exc())
            return Response(
                {"detail": "Internal server error processing prediction.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterView(generics.CreateAPIView):
    """Register a new user."""

    permission_classes = ()
    authentication_classes = ()
    serializer_class = RegisterSerializer


class PredictionHistoryView(generics.ListAPIView):
    """Paginated history of predictions for the current user."""

    serializer_class = PredictionSerializer
    filterset_fields = ["predicted_class"]
    search_fields = ["id", "predicted_class", "image_hash"]
    ordering_fields = ["created_at", "confidence_score"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Prediction.objects.filter(user=user)
        return Prediction.objects.none()


class TaskStatusView(APIView):
    """Poll the status of an async prediction task."""

    def get(self, request, task_id: str, *args, **kwargs):
        from django.conf import settings

        # In eager mode, AsyncResult doesn't store results, so check the DB
        is_eager = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)

        if not is_eager:
            result = AsyncResult(task_id)
            state = result.state

            if state in {"PENDING", "RECEIVED", "STARTED", "RETRY"}:
                return Response({"status": "processing"}, status=status.HTTP_200_OK)

            if state == "FAILURE":
                return Response(
                    {"status": "failed", "error": str(result.info)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # SUCCESS: result should be prediction_id
            try:
                prediction_id = int(result.result)
                prediction = Prediction.objects.get(id=prediction_id)
            except Exception:
                raise Http404("Prediction not found for completed task.")

            serializer = PredictionSerializer(prediction, context={"request": request})
            return Response(
                {"status": "completed", "prediction": serializer.data},
                status=status.HTTP_200_OK,
            )

        # Eager mode: look up prediction by task_id from the POST response
        # The frontend passes prediction_id as a query param
        prediction_id = request.query_params.get("prediction_id")
        if prediction_id:
            try:
                prediction = Prediction.objects.get(id=int(prediction_id))
            except Prediction.DoesNotExist:
                return Response({"status": "processing"}, status=status.HTTP_200_OK)

            # Check if prediction has been filled in (not "Unknown" anymore)
            if prediction.predicted_class != Prediction.DiseaseClass.UNKNOWN:
                serializer = PredictionSerializer(prediction, context={"request": request})
                return Response(
                    {"status": "completed", "prediction": serializer.data},
                    status=status.HTTP_200_OK,
                )

        # Fallback: try to find the most recent completed prediction
        return Response({"status": "processing"}, status=status.HTTP_200_OK)


class RecommendationView(APIView):
    """Return recommendations for a specific disease name."""

    def get(self, request, disease_name: str, *args, **kwargs):
        recs = get_disease_recommendations(disease_name)
        return Response(recs, status=status.HTTP_200_OK)


class PredictionFeedbackView(APIView):
    """Accept user correction for a prediction and save image for retraining."""

    def post(self, request, prediction_id: int, *args, **kwargs):
        import shutil
        import uuid
        from pathlib import Path
        from django.conf import settings
        from django.utils import timezone
        from .serializers import FeedbackSerializer

        try:
            prediction = Prediction.objects.get(id=prediction_id)
        except Prediction.DoesNotExist:
            return Response(
                {"detail": "Prediction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        true_class = serializer.validated_data["true_class"]

        # Update database record
        prediction.true_class = true_class
        prediction.is_corrected = True
        prediction.corrected_at = timezone.now()
        prediction.save(update_fields=["true_class", "is_corrected", "corrected_at"])

        # Copy image to training dataset for future retraining
        try:
            if prediction.image:
                source_path = Path(prediction.image.path)
                dataset_dir = (
                    Path(settings.BASE_DIR) / "dataset" / "combined" / true_class
                )
                dataset_dir.mkdir(parents=True, exist_ok=True)
                dest_name = f"feedback_{uuid.uuid4().hex}{source_path.suffix}"
                dest_path = dataset_dir / dest_name
                shutil.copy2(str(source_path), str(dest_path))
                logger.info(
                    "Copied feedback image to %s for class %s",
                    dest_path,
                    true_class,
                )
        except Exception as exc:
            logger.warning("Failed to copy feedback image to dataset: %s", exc)

        return Response(
            {
                "detail": "Feedback submitted successfully.",
                "prediction_id": prediction.id,
                "true_class": true_class,
            },
            status=status.HTTP_200_OK,
        )


class DashboardStatsView(APIView):
    """Return aggregated statistics for the dashboard."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            data = get_dashboard_stats()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error fetching dashboard stats: %s", e, exc_info=True)
            return Response(
                {"detail": "Failed to load dashboard stats.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAdminUser
from .jwt_serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """Login view that returns a JWT with custom claims (roles, permissions)."""
    serializer_class = CustomTokenObtainPairSerializer


class RetrainModelView(APIView):
    """
    API Endpoint to trigger model retraining manually.
    Only accessible by Super Admins.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        from .models import Prediction
        
        # Check if we have enough data
        corrected_count = Prediction.objects.filter(
            is_corrected=True,
            true_class__isnull=False,
        ).count()

        if corrected_count < 2:
            return Response(
                {
                    "status": "error", 
                    "detail": f"Not enough corrected predictions ({corrected_count}). Need at least 2."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trigger Celery task
        from .tasks import retrain_model_task
        task = retrain_model_task.delay()

        return Response({
            "status": "success",
            "message": "Retraining task started successfully.",
            "task_id": task.id,
            "corrected_count": corrected_count
        })


class DownloadReportView(APIView):
    """Generate and return a PDF medical report for a given prediction."""
    permission_classes = [IsAuthenticated]

    def get(self, request, prediction_id: int, *args, **kwargs):
        from django.http import FileResponse
        from .reports import generate_medical_report

        try:
            prediction = Prediction.objects.get(id=prediction_id)
        except Prediction.DoesNotExist:
            return Response(
                {"detail": "Prediction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only allow owner or admin to download
        if prediction.user and prediction.user != request.user and not request.user.is_superuser:
            try:
                if request.user.profile.role != "DOCTOR":
                    return Response(
                        {"detail": "Not authorized to view this report."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except Exception:
                return Response(
                    {"detail": "Not authorized to view this report."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            pdf_buffer = generate_medical_report(prediction)
            response = FileResponse(
                pdf_buffer,
                content_type="application/pdf",
                as_attachment=True,
                filename=f"LDD_Report_{prediction.id}.pdf",
            )
            return response
        except Exception as e:
            logger.error("PDF report generation failed: %s", e, exc_info=True)
            return Response(
                {"detail": "Failed to generate report.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
