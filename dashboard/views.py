from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import Http404
from django.utils import timezone

from listings.models import Property
from messaging.models import Inquiry, Reservation, ContactMessage, InquiryMessage


def get_dashboard_context(user):
    """
    Helper function to get dashboard counter context for any user.
    Used across all dashboard views to ensure counters are consistent.
    
    Counter logic:
    - count inquiries where user is RECEIVER (to_user) and unread
    - count inquiries where user is SENDER (from_user) and unread (meaning other person replied)
    """
    # User's listings stats
    my_listings = Property.objects.filter(owner=user).exclude(status__in=['refused', 'deleted'])
    
    # Inquiries stats - count NEW UNREAD INQUIRIES (first message from someone)
    unread_inquiries = Inquiry.objects.filter(
        to_user=user,
        to_user_read=False
    ).count()
    
    # Messages stats - count UNREAD MESSAGES in existing conversations
    # Count messages sent TO you that you haven't read yet
    unread_messages = InquiryMessage.objects.filter(
        inquiry__in=Inquiry.objects.filter(Q(to_user=user) | Q(from_user=user))
    ).exclude(sender=user).filter(is_read=False)
    
    # Total count = new inquiries + new messages
    total_unread = unread_inquiries + unread_messages.count()
    
    # Total inquiries and messages stats
    total_messages = InquiryMessage.objects.filter(
        inquiry__in=Inquiry.objects.filter(Q(to_user=user) | Q(from_user=user))
    ).count()
    
    # Reservations stats
    pending_reservations = Reservation.objects.filter(to_user=user, status='pending')
    
    # Made reservations: include all except cancelled and soft-deleted
    # (User keeps seeing rejected until they manually delete)
    made_reservations = Reservation.objects.filter(
        from_user=user
    ).exclude(
        status='cancelled'
    ).exclude(
        deleted_for_guest_at__isnull=False
    )
    
    # Received reservations: exclude rejected and cancelled
    # (Owner doesn't see rejected after rejection)
    received_reservations = Reservation.objects.filter(
        to_user=user
    ).exclude(
        status__in=['rejected', 'cancelled']
    )
    
    return {
        'my_listings_count': my_listings.count(),
        'active_listings_count': my_listings.filter(status='active').count(),
        'pending_listings_count': my_listings.filter(status='pending').count(),
        'unread_inquiries_count': total_unread,
        'total_inquiries_count': Inquiry.objects.filter(Q(to_user=user) | Q(from_user=user)).count(),
        'total_messages_count': total_messages,
        'pending_reservations_count': pending_reservations.count(),
        'total_reservations_count': made_reservations.count() + received_reservations.count(),
        'made_reservations_count': made_reservations.count(),
        'total_received_reservations_count': received_reservations.count(),
    }


class DashboardOverviewView(LoginRequiredMixin, TemplateView):
    """
    User dashboard overview showing stats and recent activity.
    """
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add counters using helper function
        context.update(get_dashboard_context(user))
        
        # User's listings stats
        my_listings = Property.objects.filter(owner=user).exclude(status__in=['refused', 'deleted'])
        
        # Recent activity
        context['recent_listings'] = my_listings.order_by('-created_at')[:5]
        context['recent_inquiries'] = Inquiry.objects.filter(to_user=user).order_by('-created_at')[:5]
        context['recent_reservations'] = Reservation.objects.filter(to_user=user).order_by('-created_at')[:5]
        
        # Tab indicator
        context['active_tab'] = self.request.GET.get('tab', 'overview')
        
        return context


class MyListingsView(LoginRequiredMixin, ListView):
    """
    Show user's property listings with edit/delete options.
    """
    template_name = 'dashboard/my_listings.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_base_queryset(self):
        """
        Base queryset of all listings for the current user.
        Excludes refused and deleted properties.
        Used both for stats and for filtered results.
        """
        return Property.objects.filter(owner=self.request.user).exclude(status__in=['refused', 'deleted']).order_by('-created_at')

    def get_queryset(self):
        """
        Apply optional status filter (?status=active|pending|reserved|sold|rented)
        on top of the base queryset.
        """
        queryset = self.get_base_queryset()
        status_filter = self.request.GET.get('status')
        if status_filter in ['active', 'pending', 'reserved', 'sold', 'rented']:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.get_base_queryset()
        
        # Add counters using helper function
        context.update(get_dashboard_context(self.request.user))

        context['active_tab'] = 'listings'
        context['status_stats'] = {
            'active': base_qs.filter(status='active').count(),
            'pending': base_qs.filter(status='pending').count(),
            'reserved': base_qs.filter(status='reserved').count(),
            'sold': base_qs.filter(status='sold').count(),
            'rented': base_qs.filter(status='rented').count(),
        }

        # Expose current status filter to the template for button highlighting
        context['current_status'] = self.request.GET.get('status', '')

        return context


class MyInboxView(LoginRequiredMixin, TemplateView):
    """
    Show user's messages and inquiries inbox.
    - Displays inquiries SENT by user (as buyer)
    - Displays inquiries RECEIVED by user (as property owner)
    """
    template_name = 'dashboard/my_inbox.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add counters using helper function
        context.update(get_dashboard_context(user))
        
        # Get inquiries RECEIVED (user is property owner)
        received_inquiries = Inquiry.objects.filter(to_user=user).order_by('-created_at').prefetch_related('messages')
        
        # Get inquiries SENT (user is the buyer)
        sent_inquiries = Inquiry.objects.filter(from_user=user).order_by('-created_at').prefetch_related('messages')
        
        # Mark as read when user views inbox (only receiver flag exists now)
        Inquiry.objects.filter(to_user=user, to_user_read=False).update(to_user_read=True)
        
        # Mark all unread messages as read (messages sent TO the user from the other person)
        all_inquiries_for_user = Inquiry.objects.filter(Q(to_user=user) | Q(from_user=user))
        InquiryMessage.objects.filter(
            inquiry__in=all_inquiries_for_user,
            is_read=False
        ).exclude(sender=user).update(is_read=True)
        
        # Combine both and sort by latest activity
        all_inquiries = list(received_inquiries) + list(sent_inquiries)
        all_inquiries.sort(key=lambda x: x.updated_at, reverse=True)
        
        # Pagination
        paginator = Paginator(all_inquiries, 20)
        page_number = self.request.GET.get('page')
        context['inquiries'] = paginator.get_page(page_number)
        context['total_inquiries'] = len(all_inquiries)
        context['unread_inquiries'] = 0  # Always 0 since we just marked all as read
        
        # Tab indicator
        context['active_tab'] = 'inbox'
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle sending a reply message."""
        user = request.user
        inquiry_id = request.POST.get('inquiry_id')
        message_text = request.POST.get('message', '').strip()
        
        if not inquiry_id or not message_text:
            messages.error(request, 'Invalid message.')
            return redirect('dashboard:inbox')
        
        try:
            inquiry = Inquiry.objects.get(id=inquiry_id)
            
            # Check if user is part of this inquiry (either sender or receiver)
            if inquiry.from_user != user and inquiry.to_user != user:
                messages.error(request, 'You are not part of this conversation.')
                return redirect('dashboard:inbox')
            
            # Create the message
            InquiryMessage.objects.create(
                inquiry=inquiry,
                sender=user,
                message=message_text,
                is_read=False  # Receiver hasn't read it yet
            )
            
            # Mark as unread for the receiver (property owner) when sender replies
            if inquiry.to_user != user:
                inquiry.to_user_read = False
            inquiry.updated_at = timezone.now()
            inquiry.save()
            
            messages.success(request, 'Message sent!')
        except Inquiry.DoesNotExist:
            messages.error(request, 'Inquiry not found.')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
        
        return redirect('dashboard:inbox')


@login_required
@require_POST
def delete_inquiry(request, inquiry_id):
    """Delete an inquiry conversation (removes from both users' inboxes)."""
    user = request.user
    
    try:
        inquiry = Inquiry.objects.get(id=inquiry_id)
        
        # Check if user is part of this inquiry (either sender or receiver)
        if inquiry.from_user != user and inquiry.to_user != user:
            messages.error(request, 'You are not part of this conversation.')
            return redirect('dashboard:inbox')
        
        # Delete the inquiry (and all its messages via cascade)
        inquiry.delete()
        messages.success(request, 'Conversation deleted successfully!')
    except Inquiry.DoesNotExist:
        messages.error(request, 'Conversation not found.')
    except Exception as e:
        messages.error(request, f'Error deleting conversation: {str(e)}')
    
    return redirect('dashboard:inbox')


class MyReservationsView(LoginRequiredMixin, TemplateView):
    """
    Show user's reservations (both made and received).
    """
    template_name = 'dashboard/my_reservations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add counters using helper function
        context.update(get_dashboard_context(user))
        
        # Received reservations (for user's properties)
        received_qs = Reservation.objects.filter(
            to_user=user
        ).exclude(status='rejected').select_related('house', 'from_user').order_by('-created_at')

        # Optional status filter (?status=pending|confirmed)
        status_filter = self.request.GET.get('status')
        if status_filter in ['pending', 'confirmed']:
            received_reservations = received_qs.filter(status=status_filter)
        else:
            received_reservations = received_qs
        
        # Made reservations (by user)
        made_qs = Reservation.objects.filter(
            from_user=user
        ).exclude(deleted_for_guest_at__isnull=False).select_related('house', 'to_user').order_by('-created_at')
        
        # Optional status filter for made (?status_made=pending|confirmed|rejected)
        status_filter_made = self.request.GET.get('status_made')
        if status_filter_made in ['pending', 'confirmed', 'rejected']:
            made_reservations = made_qs.filter(status=status_filter_made)
        else:
            made_reservations = made_qs
        
        # Pagination for received
        paginator = Paginator(received_reservations, 15)
        page_number = self.request.GET.get('page')
        context['received_reservations'] = paginator.get_page(page_number)
        context['total_received'] = received_qs.count()
        
        # Pagination for made
        paginator_made = Paginator(made_reservations, 15)
        page_number_made = self.request.GET.get('page_made')
        context['made_reservations'] = paginator_made.get_page(page_number_made)
        context['total_made'] = made_qs.count()
        
        # Status counts for received
        context['pending_count'] = received_qs.filter(status='pending').count()
        context['confirmed_count'] = received_qs.filter(status='confirmed').count()
        
        # Status counts for made
        context['made_pending_count'] = made_qs.filter(status='pending').count()
        context['made_confirmed_count'] = made_qs.filter(status='confirmed').count()
        context['made_rejected_count'] = made_qs.filter(status='rejected').count()

        # Current filter for button highlighting
        context['current_status'] = status_filter or ''
        context['current_status_made'] = status_filter_made or ''
        
        # Determine which tab should be active based on query parameters
        tab_param = self.request.GET.get('tab', '')
        if tab_param == 'made':
            context['active_tab'] = 'made'
        elif status_filter_made or page_number_made:
            context['active_tab'] = 'made'
        else:
            context['active_tab'] = 'received'
        
        # Tab indicator
        context['active_tab_name'] = 'reservations'
        
        return context


@login_required
@require_POST
def reservation_action(request, reservation_id, action):
    """
    Update reservation status from the profile area.
    Allowed actions:
    - confirm/reject by property owner (to_user)
    - cancel by guest (from_user) when pending
    """
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if action in ['confirm', 'reject']:
        if reservation.to_user != request.user:
            messages.error(request, 'You do not have permission to update this reservation.')
            return redirect('dashboard:reservations')
        if reservation.status != 'pending':
            messages.error(request, 'Only pending reservations can be updated.')
            return redirect('dashboard:reservations')
        
        if action == 'confirm':
            reservation.status = 'confirmed'
            reservation.save(update_fields=['status', 'updated_at'])
            
            # Mark property as deal done and change status to reserved
            reservation.house.deal_done = True
            reservation.house.deal_confirmed_reservation = reservation
            reservation.house.status = 'reserved'
            reservation.house.save(update_fields=['deal_done', 'deal_confirmed_reservation', 'status', 'updated_at'])
            
            # Automatically reject all other pending reservations for this property
            other_pending_reservations = Reservation.objects.filter(
                house=reservation.house,
                status='pending'
            ).exclude(id=reservation.id)
            
            if other_pending_reservations.exists():
                other_pending_reservations.update(status='rejected', updated_at=timezone.now())
            
            messages.success(request, 'Reservation confirmed. Property status changed to Reserved.')
        else:
            reservation.status = 'rejected'
            reservation.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Reservation rejected.')
        
        return redirect('dashboard:reservations')

    if action == 'cancel':
        if reservation.from_user != request.user:
            messages.error(request, 'You do not have permission to cancel this reservation.')
            return redirect('dashboard:reservations')
        if reservation.status != 'pending':
            messages.error(request, 'Only pending reservations can be cancelled.')
            return redirect('dashboard:reservations')
        reservation.delete()
        messages.success(request, 'Reservation cancelled and deleted.')
        return redirect('dashboard:reservations')

    if action == 'delete':
        # For rejected reservations by guest, or confirmed by guest
        if reservation.from_user == request.user:
            if reservation.status == 'rejected':
                # Hard delete for rejected
                reservation.delete()
                messages.success(request, 'History cleared.')
            elif reservation.status == 'confirmed':
                # Soft delete for confirmed (guest can only hide it, owner still sees it)
                reservation.deleted_for_guest_at = timezone.now()
                reservation.save(update_fields=['deleted_for_guest_at', 'updated_at'])
                messages.success(request, 'Reservation removed from your dashboard.')
        else:
            messages.error(request, 'You do not have permission to delete this reservation.')
        return redirect('dashboard:reservations')
    
    if action == 'delete_property':
        # For property owner to delete property after deal completion
        if reservation.to_user != request.user:
            messages.error(request, 'You do not have permission to delete this property.')
            return redirect('dashboard:reservations')
        if reservation.status != 'confirmed':
            messages.error(request, 'Only confirmed deals can have the property deleted.')
            return redirect('dashboard:reservations')
        
        # Delete the property
        property_title = reservation.house.title
        reservation.house.delete()
        messages.success(request, f'Property "{property_title}" has been deleted. Deal marked as complete.')
        return redirect('dashboard:reservations')

    raise Http404('Invalid reservation action.')

