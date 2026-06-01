# core/views.py - نسخه کامل‌شده
from evaluations.utils import calculate_professor_stats
from django.contrib.auth.decorators import login_required,user_passes_test
from django.shortcuts import render,get_object_or_404,redirect
from django.db.models import Avg
from courses.models import Enrollment, CourseOffering,Course
from evaluations.models import Evaluation, Appeal
from accounts.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model  

User = get_user_model()

def is_admin(user):
    return user.role == 'admin' or user.is_superuser

def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    user = request.user
    context = {}

    if user.role == "student":
        # دروس ثبت‌نام‌شده فعال
        enrollments = Enrollment.objects.filter(
            student=user,
            status="active"
        ).select_related("offering", "offering__course", "offering__professor")
        
        context["enrollments"] = enrollments
        return render(request, "core/dashboard_student.html", context)

    elif user.role == "professor":
        # دروس ارائه‌شده توسط استاد
        offerings = CourseOffering.objects.filter(
            professor=user
        ).select_related("course").prefetch_related("evaluations")

        # محاسبه میانگین نمره برای هر ارائه
        for offering in offerings:
            offering.average_rating = offering.evaluations.aggregate(
                avg=Avg("rating")
            )["avg"]

        # محاسبه میانگین کلی نمرات استاد
        average_grade = Evaluation.objects.filter(
            offering__professor=user
        ).aggregate(avg=Avg("rating"))["avg"]

        context["offerings"] = offerings
        context["average_grade"] = average_grade
        return render(request, "core/dashboard_professor.html", context)

    elif user.role == "admin":
        # آمار کلی سیستم
        stats = {
            "total_students": user.__class__.objects.filter(role="student").count(),
            "total_professors": user.__class__.objects.filter(role="professor").count(),
            "total_courses": CourseOffering.objects.count(),
            "pending_appeals": Appeal.objects.filter(status=Appeal.STATUS_PENDING).count(),
        }

        # آخرین اعتراض‌ها (5 تا)
        latest_appeals = Appeal.objects.select_related(
            "evaluation",
            "evaluation__offering",
            "evaluation__offering__professor",
            "evaluation__student"
        ).order_by("-created_at")[:5]

        context["stats"] = stats
        context["latest_appeals"] = latest_appeals
        return render(request, "core/dashboard_admin.html", context)

    # اگر نقش ناشناخته بود
    return render(request, "core/dashboard_default.html", context)


@login_required
def professor_profile(request, professor_id):
    professor = get_object_or_404(User, id=professor_id, role="professor")

    # ---- Sorting ----
    sort = request.GET.get("sort", "newest")

    if sort == "oldest":
        order = "created_at"
    elif sort == "highest":
        order = "-rating"
    elif sort == "lowest":
        order = "rating"
    else:  # newest
        order = "-created_at"

    evaluations = Evaluation.objects.filter(
        offering__professor=professor
    ).order_by(order)

    # ---- Pagination ----
    paginator = Paginator(evaluations, 5)  # هر صفحه ۵ نظر
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ---- Stats ----
    stats = calculate_professor_stats(professor)

    return render(request, "core/professor_profile.html", {
        "professor": professor,
        "stats": stats,
        "page_obj": page_obj,
        "sort": sort,
    })

@require_POST
@login_required
def ajax_submit_evaluation(request, professor_id):
    professor = get_object_or_404(User, id=professor_id, role="professor")

    # جلوگیری از ثبت چند ارزیابی برای یک استاد
    existing = Evaluation.objects.filter(
        student=request.user,
        offering__professor=professor
    ).exists()

    if existing:
        return JsonResponse({"error": "already_submitted"}, status=400)

    rating = int(request.POST.get("rating"))
    comment = request.POST.get("comment", "")

    # نکته مهم:
    # باید offering مشخص باشد. دانشجو ممکن است چند درس با این استاد داشته باشد.
    # اما فعلاً ساده نگه می‌داریم و اولین offering فعال را می‌گیریم:
    offering = CourseOffering.objects.filter(
        professor=professor
    ).first()

    if offering is None:
        return JsonResponse({"error": "no_offering_found"}, status=400)

    evaluation = Evaluation.objects.create(
        student=request.user,
        offering=offering,
        rating=rating,
        comment=comment
    )

    return JsonResponse({
        "rating": rating,
        "comment": comment,
        "created_at": evaluation.created_at.strftime("%Y-%m-%d"),
        "stars": "★" * rating
    })


def dashboard_student(request):
    current_user = request.user

    # ۱. محاسبه تعداد دقیق درس‌ها
    enrollment_count = Enrollment.objects.filter(student=current_user).count()
    
    # ۲. (اختیاری) اگر در جای دیگری از قالب به لیست enrollments نیاز داری، آن را هم نگه دار
    enrollments = Enrollment.objects.filter(student=current_user)

    return render(request, 'core/dashboard_student.html', {
        'student': current_user,
        'count': enrollment_count, # ارسال متغیر count برای نمایش عدد
        'enrollments': enrollments,
        # evaluations هم اگر استفاده نمی‌شود می‌توانی حذف کنی
    })




def dashboard_professor(request):
    # فرض می‌کنیم کاربری که لاگین کرده همان استاد است
    current_user = request.user 

    # اصلاح فیلتر: به جای professor، از offering__professor استفاده می‌کنیم
    # (باید مطمئن شوی در مدل Offering فیلدی به اسم professor داری)
    evaluations = Evaluation.objects.filter(offering__professor=current_user)

    # محاسبه میانگین (با فرض فیلد rating در Evaluation)
    from django.db.models import Avg
    avg_rating = evaluations.aggregate(Avg('rating'))['rating__avg']

    # فیلتر اعتراض‌ها برای همین استاد
    evaluations_with_appeals = evaluations.select_related('student', 'offering__course', 'appeal').filter(appeal__isnull=False)

    return render(request, 'core/dashboard_professor.html', {
        'avg_rating': avg_rating or 0,
        'evaluations_with_appeals': evaluations_with_appeals,
    })

@login_required
@user_passes_test(is_admin)
def dashboard_admin(request):
    # محاسبه آمار بر اساس نقش‌های تعریف شده در مدل User تو
    stats = {
        'total_students': User.objects.filter(role='student').count(),
        'total_professors': User.objects.filter(role='professor').count(),
        'total_courses': Course.objects.count(),
    }

    # دریافت ۵ اعتراض آخر
    latest_appeals = Appeal.objects.select_related(
        'evaluation__student', 
        'evaluation__offering__course'
    ).order_by('-id')[:5]

    return render(request, 'core/dashboard_admin.html', {
        'stats': stats,
        'latest_appeals': latest_appeals,
    })

@login_required
def redirect_dashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect('core:dashboard_admin')
    elif hasattr(request.user, 'professor_profile'): # فرض بر اینکه پروفایل استاد دارید
        return redirect('core:dashboard_professor')
    else:
        return redirect('core:dashboard_student')

def my_courses(request):
    current_user = request.user
    enrollments = Enrollment.objects.filter(student=current_user)
    return render(request, 'core/my_courses.html', {'enrollments': enrollments})
