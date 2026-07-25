from django.db.models import Avg, Count
from .models import Evaluation


# Professor statistics
def calculate_professor_stats(professor):
    # Get evaluations
    evaluations = Evaluation.objects.filter(
        offering__professor=professor
    )

    # Calculate stats
    stats = evaluations.aggregate(
        avg_overall=Avg("rating"),
        total_count=Count("id")
    )

    # Rating counts
    rating_distribution = (
        evaluations
        .values("rating")
        .annotate(count=Count("id"))
        .order_by("-rating")
    )

    # Default values
    distribution = {str(i): 0 for i in range(1, 6)}

    # Update counts
    for item in rating_distribution:
        distribution[str(item["rating"])] = item["count"]

    # Add distribution
    stats["distribution"] = distribution

    return stats