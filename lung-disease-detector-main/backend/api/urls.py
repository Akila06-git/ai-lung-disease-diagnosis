from __future__ import annotations

from django.urls import path

from .views import (
    PredictView,
    PredictionHistoryView,
    TaskStatusView,
    RecommendationView,
    PredictionFeedbackView,
    DashboardStatsView,
    RegisterView,
    CustomTokenObtainPairView,
    RetrainModelView,
    DownloadReportView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)



urlpatterns = [
    path("predict/", PredictView.as_view(), name="predict"),
    path("predictions/", PredictionHistoryView.as_view(), name="prediction-history"),
    path("task/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
    path(
        "recommendations/<str:disease_name>/",
        RecommendationView.as_view(),
        name="recommendations",
    ),
    path(
        "predictions/<int:prediction_id>/feedback/",
        PredictionFeedbackView.as_view(),
        name="prediction-feedback",
    ),
    path(
        "predictions/<int:prediction_id>/report/",
        DownloadReportView.as_view(),
        name="download-report",
    ),
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    
    # Authentication
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Admin Ops
    path("admin/retrain/", RetrainModelView.as_view(), name="retrain-model"),
]
