"""
URL configuration for the accounts app.
"""
from django.urls import path
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetCompleteView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration and Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Password Reset
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]
