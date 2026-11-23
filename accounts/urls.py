from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    path('logs/', views.log_list_view, name='log_list'),
    path('logs/new/', views.log_create_view, name='log_create'),
    path('logs/<int:pk>/', views.log_detail_view, name='log_detail'),
    path('logs/<int:pk>/edit/', views.log_update_view, name='log_update'),
    path('logs/<int:pk>/delete/', views.log_delete_view, name='log_delete'),
]