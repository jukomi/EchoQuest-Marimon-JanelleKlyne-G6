from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .decorators import role_required
from .forms import RegisterForm, ProfileForm, HabitLogForm
from .models import User, ActivityType, EmissionFactor, HabitLog


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
    all_logs = HabitLog.objects.select_related('user', 'activity_type')
    total_plastic = all_logs.aggregate(total=Sum('plastic_saved_g'))['total'] or 0
    total_co2 = all_logs.aggregate(total=Sum('co2_saved_kg'))['total'] or 0
    total_logs = all_logs.count()
    return render(request, 'accounts/admin_dashboard.html', {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
        'total_logs': total_logs,
        'total_plastic': total_plastic,
        'total_co2': total_co2,
        'recent_logs': all_logs.order_by('-created_at')[:8],
    })


@role_required(User.Role.STUDENT)
def student_dashboard(request):
    user_logs = request.user.habit_logs.select_related('activity_type')
    total_plastic = user_logs.aggregate(total=Sum('plastic_saved_g'))['total'] or 0
    total_co2 = user_logs.aggregate(total=Sum('co2_saved_kg'))['total'] or 0
    total_logs = user_logs.count()
    recent_logs = user_logs.all()[:5]
    return render(request, 'accounts/student_dashboard.html', {
        'total_plastic': total_plastic,
        'total_co2': total_co2,
        'total_logs': total_logs,
        'recent_logs': recent_logs,
    })


@login_required
def log_list_view(request):
    user_logs = request.user.habit_logs.select_related('activity_type', 'factor')
    total_plastic = user_logs.aggregate(total=Sum('plastic_saved_g'))['total'] or 0
    total_co2 = user_logs.aggregate(total=Sum('co2_saved_kg'))['total'] or 0
    total_logs = user_logs.count()
    return render(request, 'accounts/log_list.html', {
        'logs': user_logs,
        'total_plastic': total_plastic,
        'total_co2': total_co2,
        'total_logs': total_logs,
    })


@login_required
def log_create_view(request):
    form = HabitLogForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            log = form.save()
            messages.success(
                request,
                f"Logged {log.quantity} {log.activity_type.unit} of {log.activity_type.name}! Saved {log.plastic_saved_g}g plastic and reduced {log.co2_saved_kg}kg CO2."
            )
            return redirect('log_list')
        messages.error(request, 'Please correct the errors in the form.')
    return render(request, 'accounts/log_form.html', {'form': form, 'is_edit': False})


@login_required
def log_detail_view(request, pk):
    log = get_object_or_404(HabitLog.objects.select_related('activity_type', 'factor', 'user'), pk=pk)
    if log.user != request.user and request.user.role != User.Role.ADMIN:
        messages.error(request, "You do not have permission to view this log.")
        return redirect('log_list')
    can_edit = (log.user == request.user) and (log.log_date >= timezone.localdate() - timedelta(days=7))
    return render(request, 'accounts/log_detail.html', {'log': log, 'can_edit': can_edit})


@login_required
def log_update_view(request, pk):
    log = get_object_or_404(HabitLog, pk=pk)
    if log.user != request.user:
        messages.error(request, "You can only edit your own habit logs.")
        return redirect('log_list')
    if log.log_date < timezone.localdate() - timedelta(days=7):
        messages.error(request, "Logs older than 7 days can no longer be edited.")
        return redirect('log_detail', pk=pk)

    form = HabitLogForm(request.POST or None, request.FILES or None, instance=log, user=request.user)
    if request.method == 'POST':
        if form.is_valid():
            log = form.save()
            messages.success(request, f"Updated log for {log.activity_type.name}. New savings: {log.plastic_saved_g}g plastic, {log.co2_saved_kg}kg CO2.")
            return redirect('log_detail', pk=pk)
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/log_form.html', {'form': form, 'is_edit': True, 'log': log})


@login_required
def log_delete_view(request, pk):
    log = get_object_or_404(HabitLog, pk=pk)
    if log.user != request.user:
        messages.error(request, "You can only delete your own habit logs.")
        return redirect('log_list')
    if log.log_date < timezone.localdate() - timedelta(days=7):
        messages.error(request, "Logs older than 7 days can no longer be deleted.")
        return redirect('log_detail', pk=pk)

    if request.method == 'POST':
        activity_name = log.activity_type.name
        log.delete()
        messages.success(request, f"Habit log for {activity_name} was deleted.")
        return redirect('log_list')
    return render(request, 'accounts/log_confirm_delete.html', {'log': log})



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