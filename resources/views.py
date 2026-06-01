from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.utils.encoding import smart_str
from urllib.parse import quote

from .forms import ResourceForm
from .models import Resource
from courses.models import Course


@login_required
def resource_create(request):
    if request.user.role.lower() != "professor":
       return redirect("resources:resource_list")

    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            return redirect("resources:resource_list")
    else:
        form = ResourceForm()
        # اینجا هم اصلاح شد: فقط درس‌هایی که استاد واقعاً ارائه می‌دهد را در فرم نشان بده
        form.fields['course'].queryset = Course.objects.filter(offerings__professor=request.user).distinct()
    
    return render(request, "resources/resource_form.html", {"form": form})


@login_required
def resource_list(request):
    course_id = request.GET.get("course")
    role = request.user.role.lower()

    if role == "professor":
        # اصلاح فیلتر منابع: فقط منابعی که خود استاد آپلود کرده
        resources = Resource.objects.filter(uploaded_by=request.user).select_related("course").order_by("-created_at")
        
        # اصلاح فیلتر درس‌ها: درس‌هایی که این استاد در "ارائه" (Offering) آن‌ها حضور دارد
        # از offerings__professor استفاده می‌کنیم
        courses = Course.objects.filter(offerings__professor=request.user).distinct()
    else:
        # برای دانشجویان یا ادمین
        resources = Resource.objects.select_related("course").all().order_by("-created_at")
        courses = Course.objects.all()

    if course_id:
        resources = resources.filter(course_id=course_id)

    return render(request, "resources/resource_list.html", {
        "resources": resources,
        "courses": courses,
        "selected_course": course_id
    })


@login_required
def resource_download(request, pk):
    resource = get_object_or_404(Resource.objects.select_related("course", "uploaded_by"), pk=pk)

    # اگر سیاست دسترسی خاصی داری، اینجا اعمال کن.
    # فعلاً: هر کاربر لاگین‌کرده می‌تواند دانلود کند.
    if not resource.file:
        raise Http404("فایلی برای این منبع ثبت نشده است.")

    filename = resource.file.name.split("/")[-1]
    response = FileResponse(resource.file.open("rb"), as_attachment=True)
    response["Content-Disposition"] = f'attachment; filename="{smart_str(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return response
