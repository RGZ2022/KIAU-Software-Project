from django.db.models import Avg, Count
from .models import Evaluation


def calculate_professor_stats(professor):
    evaluations = Evaluation.objects.filter(offering__professor=professor)

    stats = evaluations.aggregate(
        avg_overall=Avg("rating"),
        total_count=Count("id")
    )

    rating_distribution = (
        evaluations
        .values("rating")
        .annotate(count=Count("id"))
        .order_by("-rating")
    )

    distribution = {str(i): 0 for i in range(1, 6)}

    for item in rating_distribution:
        distribution[str(item["rating"])] = item["count"]
        
    stats["distribution"] = distribution

    return stats
