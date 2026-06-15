from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Any

from .models import Prediction

def get_dashboard_stats() -> Dict[str, Any]:
    """Aggregate statistics for the dashboard."""
    
    # 1. Total Scans
    total_scans = Prediction.objects.count()

    # 2. Disease Distribution (Pie Chart)
    # Returns: [{'predicted_class': 'COVID-19', 'count': 10}, ...]
    distribution = list(
        Prediction.objects.values("predicted_class")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # 3. Recent Activity (Last 7 days) (Line Chart)
    # Returns: [{'date': datetime.date(2023, 10, 25), 'count': 5}, ...]
    seven_days_ago = timezone.now().date() - timedelta(days=6)
    daily_scans = list(
        Prediction.objects.filter(created_at__date__gte=seven_days_ago)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )
    # Convert date objects to strings for JSON serialization
    for entry in daily_scans:
        entry["date"] = entry["date"].isoformat() if entry["date"] else None


    # 4. Accuracy Metrics (based on user feedback)
    # We compare predictions where user provided feedback (is_corrected=True)
    # If is_corrected=True, it means the model was WRONG (conceptually), 
    # unless we also use feedback to confirm correct predictions (which we don't yet).
    #
    # Current logic: 
    # - Feedback provided (is_corrected=True) -> Model was WRONG.
    # - No feedback -> user accepted result (implicitly CORRECT? or just didn't bother).
    # This is a naive metric but best we have without ground truth for everything.
    
    total_feedback = Prediction.objects.filter(is_corrected=True).count()
    
    # Let's count "Critical Found" (COVID + TB)
    critical_cases = Prediction.objects.filter(
        Q(predicted_class=Prediction.DiseaseClass.COVID19) | 
        Q(predicted_class=Prediction.DiseaseClass.TUBERCULOSIS)
    ).count()

    return {
        "total_scans": total_scans,
        "critical_cases": critical_cases,
        "reported_errors": total_feedback,
        "disease_distribution": distribution,
        "daily_scans": daily_scans,
    }
