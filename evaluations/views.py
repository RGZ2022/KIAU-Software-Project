from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseNotAllowed
from django.contrib import messages
from django.utils import timezone

from courses.models import CourseOffering, Enrollment
from .models import Evaluation, Appeal
from .forms import EvaluationForm, AppealForm, AppealStatusForm


# آدرس داشبورد
DASHBOARD_URL = "core:dashboard"


@login_required
def evaluate_professor(request, offering_id):
    offering = get_object_or_404(CourseOffering, id=offering_id)

    # فقط دانشجوی ثبت‌نام شده فعال
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        offering=offering,
        status="active"
    ).exists()

    if not is_enrolled:
        return render(request, "evaluations/not_allowed.html", {
            "message": "شما اجازه دسترسی به این بخش را ندارید."
        }, status=403)

    # جلوگیری از ارزیابی دوباره
    if Evaluation.objects.filter(offering=offering, student=request.user).exists():
        return render(request, "evaluations/already_done.html", {
            "offering_id": offering.id,
            "message": "شما قبلاً این درس را ارزیابی کرده‌اید."
        }, status=403)

    if request.method == "POST":
        form = EvaluationForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.offering = offering
            ev.student = request.user
            ev.save()

            messages.success(request, "ارزیابی با موفقیت ثبت شد.")
            return redirect(DASHBOARD_URL)
    else:
        form = EvaluationForm()

    # در ویوی evaluate_professor
    return render(request, "evaluations/evaluate_form.html", {
     "form": form,
     "offering": offering,
     "professor_name": offering.professor.get_full_name()  # اضافه کردن این خط
     })



@login_required
def appeal_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    # فقط استاد همان درس
    if evaluation.offering.professor != request.user:
        return render(request, "evaluations/not_allowed.html", {
            "message": "این ارزیابی متعلق به شما نیست."
        }, status=403)

    # جلوگیری از اعتراض دوباره
    if hasattr(evaluation, "appeal"):
        return render(request, "evaluations/already_appealed.html", {
            "evaluation": evaluation,
            "offering_id": evaluation.offering.id,
            "message": "برای این ارزیابی قبلاً اعتراض ثبت شده است."
        }, status=403)

    if request.method == "POST":
        form = AppealForm(request.POST)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.evaluation = evaluation
            appeal.save()

            messages.success(request, "اعتراض با موفقیت ثبت شد.")
            return redirect(DASHBOARD_URL)
    else:
        form = AppealForm()

    return render(request, "evaluations/appeal_form.html", {
        "form": form,
        "evaluation": evaluation,
        "offering_id": evaluation.offering.id,
    })



@login_required
def admin_appeals_list(request):
    if request.user.role != "admin":
        return render(request, "evaluations/not_allowed.html", status=403)

    appeals = Appeal.objects.select_related(
        "evaluation",
        "evaluation__offering",
        "evaluation__offering__professor",
        "evaluation__student",
    ).order_by("-id")

    return render(request, "evaluations/admin_appeals_list.html", {
        "appeals": appeals,
        "list_type": "all",
    })


@login_required
def admin_pending_appeals_list(request):
    if request.user.role != "admin":
        return render(request, "evaluations/not_allowed.html", status=403)

    appeals = Appeal.objects.select_related(
        "evaluation",
        "evaluation__offering",
        "evaluation__offering__professor",
        "evaluation__student",
    ).filter(status="pending").order_by("-id")

    return render(request, "evaluations/admin_appeals_list.html", {
        "appeals": appeals,
        "list_type": "pending",
    })


@login_required
def update_appeal_status(request, appeal_id):

    if request.user.role != "admin":
        return render(request, "evaluations/not_allowed.html", status=403)

    appeal = get_object_or_404(Appeal, id=appeal_id)

    if appeal.lock_if_decided():
        messages.error(request, "این اعتراض قبلاً تعیین تکلیف شده است.")
        return redirect("evaluations:admin_appeals_list")

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    old_status = appeal.status

    form = AppealStatusForm(request.POST, instance=appeal)
    if form.is_valid():
        updated_appeal = form.save(commit=False)

        if (
            old_status == Appeal.STATUS_PENDING and
            updated_appeal.status in [Appeal.STATUS_ACCEPTED, Appeal.STATUS_REJECTED]
        ):
            updated_appeal.decided_at = timezone.now()

        updated_appeal.save()
        messages.success(request, "وضعیت اعتراض با موفقیت بروزرسانی شد.")
    else:
        messages.error(request, "فرم معتبر نیست.")

    return redirect("evaluations:admin_appeals_list")

@login_required
def professor_evaluations_list(request, offering_id):

    # فقط استاد صاحب درس اجازه دارد
    offering = get_object_or_404(
        CourseOffering,
        id=offering_id,
        professor=request.user
    )

    # دریافت همه ارزیابی‌های ثبت‌شده برای این درس
    evaluations = (
        Evaluation.objects
        .filter(offering=offering)
        .order_by("-id")
    )

    # آماده‌سازی داده‌ها بدون نمایش هویت دانشجو
    eval_list = []
    counter = 1
    for ev in evaluations:
        eval_list.append({
            "anon_name": f"دانشجو #{counter}",
            "score": ev.rating,
            "comment": ev.comment,
            "id": ev.id,
            "appeal_exists": hasattr(ev, "appeal"),
        })
        counter += 1

    return render(request, "evaluations/professor_evaluations_list.html", {
        "offering": offering,
        "evaluations": eval_list,
    })
