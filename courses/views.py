from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from django.contrib import messages
from django.urls import reverse
from .forms import OfferingForm


from .models import Course, CourseOffering, Enrollment

def is_student(u):
    return u.is_authenticated and u.role == "student"

def is_professor(u):
    return u.is_authenticated and u.role == "professor"

def is_admin(u):
    return u.is_authenticated and u.role == "admin"


# 1) لیست همه ارائه‌ها (فیلتر ترم)
def course_offerings_list(request):
    term = request.GET.get("term")  # مثل 1405-1
    qs = CourseOffering.objects.select_related("course", "professor")

    if term:
        qs = qs.filter(term=term)

    context = {
        "offerings": qs,
        "term": term or "",
    }
    return render(request, "courses/course_offerings_list.html", context)


# 2) جزئیات هر درس + ارائه‌ها
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    offerings = course.offerings.all()
    # اضافه کردن منابع مرتبط با این درس
    resources = course.resources.all() 
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'offerings': offerings,
        'resources': resources, # پاس دادن منابع به تمپلیت
    })


# 3) لیست ارائه‌های استاد
@login_required
@user_passes_test(is_professor)
def professor_offerings_list(request):
    offerings = CourseOffering.objects.filter(
        professor=request.user
    ).select_related("course")
    return render(request, "courses/professor_offerings_list.html", {"offerings": offerings})


# 4) ثبت‌نام دانشجو در ارائه
@login_required
@user_passes_test(is_student)
def enroll_in_offering(request, offering_id):
    offering = get_object_or_404(CourseOffering, id=offering_id)

    if not offering.is_active:
        messages.error(request, "این ارائه غیرفعال است.")
        return redirect("courses:offerings_list")

    # ظرفیت
    active_count = offering.enrollments.filter(status="active").count()
    if active_count >= offering.capacity:
        messages.error(request, "ظرفیت این ارائه تکمیل است.")
        return redirect("courses:offerings_list")

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        offering=offering,
        defaults={"status": "active"}
    )

    # اگر قبلاً dropped بوده، دوباره فعال شود
    if not created and enrollment.status == "dropped":
        enrollment.status = "active"
        enrollment.save()
        messages.success(request, "ثبت‌نام شما دوباره فعال شد.")
    elif created:
        messages.success(request, "ثبت‌نام با موفقیت انجام شد.")

    return redirect("courses:my_enrollments")


# 5) لیست ثبت‌نام‌های دانشجو
@login_required
@user_passes_test(is_student)
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related("offering__course", "offering__professor")
    return render(request, "courses/my_enrollments.html", {"enrollments": enrollments})


# 6) پنل مدیریت ارائه‌ها (ادمین)
@login_required
@user_passes_test(is_admin)
def admin_offerings_panel(request):
    term = request.GET.get("term")
    qs = CourseOffering.objects.select_related("course", "professor")
    if term:
        qs = qs.filter(term=term)
    return render(request, "courses/admin_offerings_panel.html", {"offerings": qs, "term": term or ""})

@login_required
@user_passes_test(is_professor)
def offering_students_list(request, offering_id):
    offering = get_object_or_404(
        CourseOffering.objects.select_related("course", "professor"),
        id=offering_id,
        professor=request.user,  # فقط ارائه‌های خودش
    )

    enrollments = (
        Enrollment.objects
        .filter(offering=offering)
        .select_related("student")
        .order_by("student__username")
    )

    return render(
        request,
        "courses/offering_students_list.html",
        {"offering": offering, "enrollments": enrollments},
    )

@login_required
@user_passes_test(is_admin)
def admin_offering_create(request):
    if request.method == "POST":
        form = OfferingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "ارائه جدید با موفقیت ایجاد شد.")
            return redirect("courses:admin_offerings")
    else:
        form = OfferingForm()

    return render(request, "courses/admin_offering_form.html", {
        "form": form,
        "mode": "create"
    })


@login_required
@user_passes_test(is_admin)
def admin_offering_update(request, offering_id):
    offering = get_object_or_404(CourseOffering, id=offering_id)

    if request.method == "POST":
        form = OfferingForm(request.POST, instance=offering)
        if form.is_valid():
            form.save()
            messages.success(request, "ارائه با موفقیت ویرایش شد.")
            return redirect("courses:admin_offerings")
    else:
        form = OfferingForm(instance=offering)

    return render(request, "courses/admin_offering_form.html", {
        "form": form,
        "mode": "edit",
        "offering": offering
    })


@login_required
@user_passes_test(is_admin)
def admin_offering_delete(request, offering_id):
    offering = get_object_or_404(CourseOffering, id=offering_id)

    if request.method == "POST":
        offering.delete()
        messages.success(request, "ارائه حذف شد.")
        return redirect("courses:admin_offerings")

    return render(request, "courses/admin_offering_confirm_delete.html", {
        "offering": offering
    })
