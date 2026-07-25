from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.utils.encoding import smart_str
from urllib.parse import quote
from .forms import ResourceForm
from .models import Resource
from courses.models import Course


# Create resource
@login_required
def resource_create(request):

    # Professor check
    if request.user.role.lower() != "professor":
        return redirect("resources:resource_list")

    if request.method == "POST":
        # Form data
        form = ResourceForm(request.POST, request.FILES)

        if form.is_valid():
            # Save resource
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()

            return redirect("resources:resource_list")

    else:
        # Empty form
        form = ResourceForm()

        # Available courses
        form.fields["course"].queryset = (
            Course.objects.filter(
                offerings__professor=request.user
            ).distinct()
        )

    return render(
        request,
        "resources/resource_form.html",
        {"form": form}
    )


# Resource list
@login_required
def resource_list(request):

    # Filter value
    course_id = request.GET.get("course")
    role = request.user.role.lower()

    # Professor resources
    if role == "professor":
        resources = (
            Resource.objects
            .filter(uploaded_by=request.user)
            .select_related("course")
            .order_by("-created_at")
        )

        # Professor courses
        courses = (
            Course.objects
            .filter(offerings__professor=request.user)
            .distinct()
        )

    # Other users
    else:
        resources = (
            Resource.objects
            .select_related("course")
            .all()
            .order_by("-created_at")
        )

        courses = Course.objects.all()

    # Course filter
    if course_id:
        resources = resources.filter(course_id=course_id)

    return render(
        request,
        "resources/resource_list.html",
        {
            "resources": resources,
            "courses": courses,
            "selected_course": course_id,
        }
    )


# Download resource
@login_required
def resource_download(request, pk):

    # Get resource
    resource = get_object_or_404(
        Resource.objects.select_related(
            "course",
            "uploaded_by"
        ),
        pk=pk
    )

    # File check
    if not resource.file:
        raise Http404(
            "فایلی برای این منبع ثبت نشده است."
        )

    # File response
    filename = resource.file.name.split("/")[-1]

    response = FileResponse(
        resource.file.open("rb"),
        as_attachment=True
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="{smart_str(filename)}"; '
        f"filename*=UTF-8''{quote(filename)}"
    )

    return response