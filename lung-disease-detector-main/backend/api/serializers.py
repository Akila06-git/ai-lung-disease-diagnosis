from __future__ import annotations

from rest_framework import serializers

from .models import Prediction
from django.contrib.auth import get_user_model

User = get_user_model()


class PredictionSerializer(serializers.ModelSerializer):
    """Serializer exposing all prediction fields plus convenience helpers."""

    image_url = serializers.SerializerMethodField()
    heatmap_image_url = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Prediction
        fields = [
            "id",
            "image",
            "image_url",
            "image_hash",
            "patient_name",
            "patient_age",
            "patient_sex",
            "symptoms",
            "predicted_class",
            "confidence_score",
            "confidence_percentage",
            "urgency_level",
            "urgency_color",
            "urgency_icon",
            "immediate_actions",
            "medical_recommendations",
            "lifestyle_recommendations",
            "follow_up",
            "disclaimer",
            "created_at",
            "processing_time_ms",
            "cached_result",
            "true_class",
            "is_corrected",
            "corrected_at",
            "heatmap_image",
            "heatmap_image_url",
        ]
        read_only_fields = [
            "id",
            "image_url",
            "image_hash",
            "created_at",
            "processing_time_ms",
            "cached_result",
            "true_class",
            "is_corrected",
            "corrected_at",
            "heatmap_image",
            "heatmap_image_url",
        ]

    def get_image_url(self, obj: Prediction) -> str | None:
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request is not None else url

    def get_heatmap_image_url(self, obj: Prediction) -> str | None:
        request = self.context.get("request")
        if not obj.heatmap_image:
            return None
        url = obj.heatmap_image.url
        return request.build_absolute_uri(url) if request is not None else url

    def get_confidence_percentage(self, obj: Prediction) -> float:
        return obj.confidence_percentage


class FeedbackSerializer(serializers.Serializer):
    """Accepts a user correction for a prediction."""

    true_class = serializers.ChoiceField(
        choices=Prediction.DiseaseClass.choices,
        help_text="The correct disease class for this X-ray.",
    )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""

    class Meta:
        model = User
        fields = ("id", "username", "email")


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    role = serializers.CharField(write_only=True, required=False, default="PATIENT")

    class Meta:
        model = User
        fields = ("username", "password", "email", "role")

    def create(self, validated_data):
        role_data = validated_data.pop("role", "PATIENT")
        
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )
        
        # Create the profile and attach the role
        from .models import UserProfile
        UserProfile.objects.create(user=user, role=role_data)
        
        return user

