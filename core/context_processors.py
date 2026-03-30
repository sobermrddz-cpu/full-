"""
Context processors for core app.
Injects commonly needed variables into all templates.
"""
from django.db.models import Q
from messaging.models import Inquiry, Reservation, InquiryMessage


def unread_counts(request):
    """
    Inject unread message and reservation counts into template context.
    Only available for authenticated users.
    """
    context = {
        'unread_inquiries': 0,
        'unread_reservations': 0,
        'unread_contacts': 0,
        'pending_reservations': 0,
    }

    if request.user and request.user.is_authenticated:
        # Count unread inquiries (NEW inquiries that user hasn't read)
        unread_inquiries = Inquiry.objects.filter(
            to_user=request.user,
            to_user_read=False
        ).count()
        
        # Count unread inquiry messages (replies in conversations)
        unread_messages = InquiryMessage.objects.filter(
            inquiry__in=Inquiry.objects.filter(Q(to_user=request.user) | Q(from_user=request.user))
        ).exclude(sender=request.user).filter(is_read=False).count()
        
        # Count pending reservations (awaiting user's approval)
        pending_reservations = Reservation.objects.filter(
            to_user=request.user,
            status='pending'
        ).count()
        
        # Count total reservations (made + received)
        made_reservations = Reservation.objects.filter(
            from_user=request.user
        ).count()
        received_reservations = Reservation.objects.filter(
            to_user=request.user
        ).count()
        
        context['unread_inquiries'] = unread_inquiries + unread_messages
        context['pending_reservations'] = pending_reservations
        context['unread_reservations'] = pending_reservations
        context['total_reservations'] = made_reservations + received_reservations

    return context
