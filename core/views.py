from evaluations.utils import calculate_professor_stats
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg
from courses.models import Enrollment, CourseOffering, Course
from evaluations.models import Evaluation, Appeal
from accounts.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

User = get_user_model()


# Admin check
def is_admin(user):
    return user.role == 'admin' or user.is_superuser


# Home
def home(request):
    return render(request, 'core/home.html')


# Dashboard
@login_required
def dashboard(request):
    user = request.user
    context = {}

    # Student
    if user.role == "student":
        # Active enrollments
        enrollments = Enrollment.objects.filter(
            student=user,
            status="active"
        ).select_related(
            "offering",
            "offering__course",
            "offering__professor"
        )

        context["enrollments"] = enrollments
        return render(request, "core/dashboard_student.html", context)

    # Professor
    elif user.role == "professor":
        # Course offerings
        offerings = CourseOffering.objects.filter(
            professor=user
        ).select_related("course").prefetch_related("evaluations")

        # Average rating
        for offering in offerings:
            offering.average_rating = offering.evaluations.aggregate(
                avg=Avg("rating")
            )["avg"]

        # Overall rating
        average_grade = Evaluation.objects.filter(
            offering__professor=user
        ).aggregate(avg=Avg("rating"))["avg"]

        context["offerings"] = offerings
        context["average_grade"] = average_grade

        return render(request, "core/dashboard_professor.html", context)

    # Admin
    elif user.role == "admin":
        # Statistics
        stats = {
            "total_students": user.__class__.objects.filter(role="student").count(),
            "total_professors": user.__class__.objects.filter(role="professor").count(),
            "total_courses": CourseOffering.objects.count(),
            "pending_appeals": Appeal.objects.filter(
                status=Appeal.STATUS_PENDING
            ).count(),
        }

        # Latest appeals
        latest_appeals = Appeal.objects.select_related(
            "evaluation",
            "evaluation__offering",
            "evaluation__offering__professor",
            "evaluation__student"
        ).order_by("-created_at")[:5]

        context["stats"] = stats
        context["latest_appeals"] = latest_appeals

        return render(request, "core/dashboard_admin.html", context)

    # Default
    return render(request, "core/dashboard_default.html", context)
# Professor profile
@login_required
def professor_profile(request, professor_id):
    # Get professor
    professor = get_object_or_404(
        User,
        id=professor_id,
        role="professor"
    )

    # Sort
    sort = request.GET.get("sort", "newest")

    if sort == "oldest":
        order = "created_at"
    elif sort == "highest":
        order = "-rating"
    elif sort == "lowest":
        order = "rating"
    else:
        order = "-created_at"

    # Evaluations
    evaluations = (
        Evaluation.objects
        .filter(offering__professor=professor)
        .order_by(order)
    )

    # Pagination
    paginator = Paginator(evaluations, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistics
    stats = calculate_professor_stats(professor)

    # Student offering
    offering = None

    if request.user.is_authenticated and request.user.role == "student":

        enrollment = (
            Enrollment.objects
            .filter(
                student=request.user,
                status="active",
                offering__professor=professor
            )
            .select_related("offering")
            .first()
        )

        if enrollment:
            offering = enrollment.offering

    return render(request, "core/professor_profile.html", {
        "professor": professor,
        "stats": stats,
        "page_obj": page_obj,
        "sort": sort,
        "offering": offering,
    })


# Ajax evaluation
@require_POST
@login_required
def ajax_submit_evaluation(request, professor_id):
    # Get professor
    professor = get_object_or_404(
        User,
        id=professor_id,
        role="professor"
    )

    # Duplicate check
    existing = Evaluation.objects.filter(
        student=request.user,
        offering__professor=professor
    ).exists()

    if existing:
        return JsonResponse(
            {"error": "already_submitted"},
            status=400
        )

    # Form data
    rating = int(request.POST.get("rating"))
    comment = request.POST.get("comment", "")

    # Get offering
    offering = CourseOffering.objects.filter(
        professor=professor
    ).first()

    if offering is None:
        return JsonResponse(
            {"error": "no_offering_found"},
            status=400
        )

    # Save evaluation
    evaluation = Evaluation.objects.create(
        student=request.user,
        offering=offering,
        rating=rating,
        comment=comment
    )

    # Response
    return JsonResponse({
        "rating": rating,
        "comment": comment,
        "created_at": evaluation.created_at.strftime("%Y-%m-%d"),
        "stars": "★" * rating
    })

# Student dashboard
def dashboard_student(request):
    # Current user
    current_user = request.user

    # Enrollment count
    enrollment_count = Enrollment.objects.filter(
        student=current_user
    ).count()

    # Enrollments
    enrollments = Enrollment.objects.filter(
        student=current_user
    )

    return render(request, 'core/dashboard_student.html', {
        'student': current_user,
        'count': enrollment_count,
        'enrollments': enrollments,
    })


# Professor dashboard
def dashboard_professor(request):
    # Current user
    current_user = request.user

    # Evaluations
    evaluations = Evaluation.objects.filter(
        offering__professor=current_user
    )

    # Average rating
    from django.db.models import Avg
    avg_rating = evaluations.aggregate(
        Avg('rating')
    )['rating__avg']

    # Appeals
    evaluations_with_appeals = evaluations.select_related(
        'student',
        'offering__course',
        'appeal'
    ).filter(
        appeal__isnull=False
    )

    return render(request, 'core/dashboard_professor.html', {
        'avg_rating': avg_rating or 0,
        'evaluations_with_appeals': evaluations_with_appeals,
    })


# Admin dashboard
@login_required
@user_passes_test(is_admin)
def dashboard_admin(request):
    # Statistics
    stats = {
        'total_students': User.objects.filter(
            role='student'
        ).count(),
        'total_professors': User.objects.filter(
            role='professor'
        ).count(),
        'total_courses': Course.objects.count(),
    }

    # Latest appeals
    latest_appeals = Appeal.objects.select_related(
        'evaluation__student',
        'evaluation__offering__course'
    ).order_by('-id')[:5]

    return render(request, 'core/dashboard_admin.html', {
        'stats': stats,
        'latest_appeals': latest_appeals,
    })


# Redirect dashboard
@login_required
def redirect_dashboard(request):
    # Admin
    if request.user.is_superuser or request.user.is_staff:
        return redirect('core:dashboard_admin')

    # Professor
    elif hasattr(request.user, 'professor_profile'):
        return redirect('core:dashboard_professor')

    # Student
    else:
        return redirect('core:dashboard_student')


# My courses
def my_courses(request):
    # Current user
    current_user = request.user

    # Enrollments
    enrollments = Enrollment.objects.filter(
        student=current_user
    )

    return render(request, 'core/my_courses.html', {
        'enrollments': enrollments
    })