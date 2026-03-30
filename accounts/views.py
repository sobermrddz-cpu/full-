"""
Views for the accounts app.
Handles user authentication, registration, profile management, and password reset.
"""
from django.shortcuts import render, redirect
from django.views.generic import CreateView, UpdateView, View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .forms import RegisterForm, LoginForm, ProfileForm

User = get_user_model()


class RegisterView(CreateView):
    """
    User registration view.
    Creates a new CustomUser account.
    """
    model = User
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """
        Save the user and show success message.
        """
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Registration successful! Please log in with your credentials.'
        )
        return response


class LoginView(View):
    """
    User login view.
    Supports authentication with username or email.
    Blocks banned users.
    """
    template_name = 'accounts/login.html'

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def dispatch(self, request, *args, **kwargs):
        """
        Rate limit login attempts to 5 per minute.
        """
        if request.user.is_authenticated:
            return redirect('listings:home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Display login form."""
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle login form submission."""
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate using custom backend (supports username or email)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Check if user is banned
                if user.is_banned:
                    messages.error(
                        request,
                        'Your account has been banned. Please contact support.'
                    )
                    return render(request, self.template_name, {'form': form})

                # Check if user is active
                if not user.is_active:
                    messages.error(
                        request,
                        'Your account is inactive. Please contact support.'
                    )
                    return render(request, self.template_name, {'form': form})

                # Login successful
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')

                # Redirect to next URL or default to home
                next_url = request.GET.get('next', 'listings:home')
                return redirect(next_url)
            else:
                # Invalid credentials
                messages.error(
                    request,
                    'Invalid username/email or password. Please try again.'
                )

        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """
    User logout view.
    Must be accessed via POST to prevent accidental logout via links.
    """

    def post(self, request):
        """Handle logout."""
        username = request.user.get_full_name() if request.user.is_authenticated else 'User'
        logout(request)
        messages.success(request, f'You have been logged out successfully.')
        return redirect('listings:home')


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    User profile edit view.
    Allows users to update their profile information.
    """
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        """Return the current user."""
        return self.request.user

    def form_valid(self, form):
        """Handle form submission."""
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully!')
        return response


class PasswordResetView(PasswordResetView):
    """
    Custom password reset view extending Django's built-in view.
    """
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirm view extending Django's built-in view.
    """
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
