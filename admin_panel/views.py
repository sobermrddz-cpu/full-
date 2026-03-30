from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from listings.models import Property
from messaging.models import ContactMessage, Inquiry, Reservation
from accounts.models import CustomUser

User = get_user_model()


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin to require staff access to the custom admin panel.
    Non-authenticated users are redirected to login,
    authenticated non-staff users are redirected to the home page
    with an error message.
    """

    def test_func(self):
        return self.request.user.is_staff and self.request.user.is_active

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            login_url = f"{reverse('accounts:login')}?next={self.request.path}"
            return redirect(login_url)

        messages.error(
            self.request,
            "You don't have permission to access the admin panel."
        )
        return redirect('listings:home')


class AdminPanelOverviewView(StaffRequiredMixin, TemplateView):
    """
    Admin panel overview dashboard.
    """
    template_name = 'admin_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stats - Count only active/relevant items
        context['total_users'] = CustomUser.objects.filter(is_superuser=False).count()
        context['total_properties'] = Property.objects.exclude(status__in=['deleted', 'refused']).count()
        context['active_properties'] = Property.objects.filter(status='active').count()
        context['pending_properties'] = Property.objects.filter(status='pending').count()
        context['refused_properties'] = Property.objects.filter(status='refused').count()
        context['total_inquiries'] = Inquiry.objects.count()
        context['unread_inquiries'] = Inquiry.objects.filter(to_user_read=False).count()
        # Count only active and pending reservations (not rejected or confirmed)
        context['total_reservations'] = Reservation.objects.filter(status='pending').count()
        context['pending_reservations'] = Reservation.objects.filter(status='pending').count()
        context['total_messages'] = ContactMessage.objects.count()
        context['unread_messages'] = ContactMessage.objects.filter(is_read=False).count()
        
        # Recent activity
        context['recent_users'] = CustomUser.objects.filter(is_superuser=False).order_by('-date_joined')[:2]
        context['recent_properties'] = Property.objects.exclude(status__in=['deleted', 'refused']).order_by('-created_at')[:2]
        context['recent_messages'] = ContactMessage.objects.order_by('-created_at')[:2]
        
        # Tab indicator
        context['active_tab'] = self.request.GET.get('tab', 'overview')
        
        return context


class ListingsManagerView(StaffRequiredMixin, ListView):
    """
    Manage all property listings.
    """
    model = Property
    template_name = 'admin_panel/listings_manager.html'
    context_object_name = 'listings'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Property.objects.exclude(status__in=['deleted', 'refused']).order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'listings'
        context['status_stats'] = {
            'pending': Property.objects.filter(status='pending').count(),
            'active': Property.objects.filter(status='active').count(),
            'reserved': Property.objects.filter(status='reserved').count(),
            'refused': Property.objects.filter(status='refused').count(),
            'deleted': Property.objects.filter(status='deleted').count(),
        }
        return context


class PropertyApproveView(StaffRequiredMixin, View):
    """
    Approve a pending property listing (set status to 'active').
    """

    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        prop.status = 'active'
        prop.save(update_fields=['status'])
        messages.success(request, f"Property '{prop.title}' has been approved and is now active.")
        return redirect('admin_panel:listings')


class PropertyRejectView(StaffRequiredMixin, View):
    """
    Reject a pending property listing (set status to 'refused').
    """

    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        prop.status = 'refused'
        prop.save(update_fields=['status'])
        messages.warning(request, f"Property '{prop.title}' has been refused.")
        return redirect('admin_panel:listings')


class UsersManagerView(StaffRequiredMixin, ListView):
    """
    Manage all users including admins.
    """
    model = CustomUser
    template_name = 'admin_panel/users_manager.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('-date_joined')
        
        # Filter
        filter_type = self.request.GET.get('filter')
        if filter_type == 'banned':
            queryset = queryset.filter(is_banned=True)
        elif filter_type == 'admin':
            queryset = queryset.filter(is_staff=True)
        elif filter_type == 'active':
            queryset = queryset.filter(is_banned=False, is_staff=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'users'
        context['total_users'] = CustomUser.objects.count()
        context['active_users'] = CustomUser.objects.filter(is_banned=False, is_staff=False).count()
        context['banned_users'] = CustomUser.objects.filter(is_banned=True).count()
        context['admin_users'] = CustomUser.objects.filter(is_staff=True).count()
        return context


class UserBanToggleView(StaffRequiredMixin, View):
    """
    Ban or unban a user. If banning, log out the user if they're currently logged in.
    """

    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pk):
        from django.contrib.auth import logout
        from django.contrib.sessions.models import Session
        
        user = get_object_or_404(CustomUser, pk=pk)

        if user.is_superuser:
            messages.error(request, "Cannot ban or unban superuser accounts.")
            return redirect('admin_panel:users')
        
        # Toggle ban status
        user.is_banned = not user.is_banned
        user.save(update_fields=['is_banned'])
        
        if user.is_banned:
            # Log out the user if they're currently logged in
            # Find and delete their active session
            for session in Session.objects.all():
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user.id):
                    session.delete()
            
            messages.warning(request, f"User '{user.username}' has been banned and logged out.")
        else:
            messages.success(request, f"User '{user.username}' has been unbanned.")
        
        return redirect('admin_panel:users')


class UserDeleteView(StaffRequiredMixin, View):
    """
    Delete a user permanently.
    """

    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pk):
        from django.contrib.sessions.models import Session
        from django.contrib.auth import logout
        
        user = get_object_or_404(CustomUser, pk=pk)
        username = user.username
        is_admin = user.is_staff
        is_self = (user == request.user)
        
        # Log out the user if they're currently logged in (delete their active session)
        for session in Session.objects.all():
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                session.delete()
        
        user.delete()
        
        # Customized success message based on user type
        if is_admin:
            if is_self:
                messages.success(request, f"Your admin account has been permanently deleted. You have been logged out.")
            else:
                messages.success(request, f"Admin account '{username}' has been permanently deleted and logged out.")
        else:
            if is_self:
                messages.success(request, f"Your account has been permanently deleted. You have been logged out.")
            else:
                messages.success(request, f"User '{username}' has been permanently deleted.")
        
        # If user deleted their own account, redirect to home after logout
        if is_self:
            return redirect('listings:home')
        
        return redirect('admin_panel:users')


class ContactsInboxView(StaffRequiredMixin, ListView):
    """
    View all contact form messages.
    """
    model = ContactMessage
    template_name = 'admin_panel/contacts_inbox.html'
    context_object_name = 'contact_messages'
    paginate_by = 20
    
    def get_queryset(self):
        return ContactMessage.objects.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'contacts'
        context['total_messages'] = ContactMessage.objects.count()
        context['unread_messages'] = ContactMessage.objects.filter(is_read=False).count()
        return context


class ContactMessageDeleteView(StaffRequiredMixin, View):
    """
    Delete a contact message (hard delete).
    """

    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pk):
        message = get_object_or_404(ContactMessage, pk=pk)
        message.delete()
        messages.success(request, "Message has been permanently deleted.")
        return redirect('admin_panel:contacts')



