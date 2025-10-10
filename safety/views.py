from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import SafetyReport
from .forms import SafetyReportForm


def safety_list(request):
    reports = SafetyReport.objects.all()
    return render(request, 'safety/safety_list.html', {'reports': reports})


def safety_detail(request, pk):
    report = get_object_or_404(SafetyReport, pk=pk)
    return render(request, 'safety/safety_detail.html', {'report': report})


@login_required
def safety_create(request):
    if request.method == 'POST':
        form = SafetyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            return redirect('safety:safety_detail', pk=report.pk)
    else:
        form = SafetyReportForm()
    return render(request, 'safety/safety_form.html', {'form': form})


def guidelines_index(request):
    """Overview page linking to individual safety guideline pages."""
    return render(request, 'safety/guidelines/index.html')


def verify_before_meeting(request):
    return render(request, 'safety/guidelines/verify_before_meeting.html')


def share_location(request):
    return render(request, 'safety/guidelines/share_location.html')


def emergency_support(request):
    return render(request, 'safety/guidelines/emergency_support.html')
# (safety views are defined above)
