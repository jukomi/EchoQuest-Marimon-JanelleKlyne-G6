from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .decorators import role_required
from .forms import RegisterForm, ProfileForm
from .models import User


def home(request):
    return redirect('dashboard_redirect' if request.user.is_authenticated else 'login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! You can now log in.')
            return redirect('login')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_redirect(request):
    if request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    return redirect('student_dashboard')


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html', {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
    })


@role_required(User.Role.STUDENT)
def student_dashboard(request):
    return render(request, 'accounts/student_dashboard.html')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'profile_user': request.user})


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/profile_edit.html', {'form': form})