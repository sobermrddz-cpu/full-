from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import Http404
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone

from listings.models import Property
from .models import Inquiry, Reservation, ContactMessage, InquiryMessage
from .forms import ContactForm, InquiryForm, ReservationForm


class ContactFormView(FormView):
    """
    Handle general contact form submissions.
    No login required for regular users.
    Staff members cannot access this form (they are the ones being contacted).
    """
    template_name = 'messaging/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('messaging:contact')  # Stay on contact page to show success message

    def dispatch(self, request, *args, **kwargs):
        """Prevent staff/admin users from submitting contact forms."""
        if request.user.is_authenticated and request.user.is_staff:
            messages.info(
                request,
                'Staff members cannot submit contact form messages. Please use the admin panel instead.'
            )
            return redirect('listings:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Save contact message and show success."""
        form.save()
        messages.success(
            self.request,
            '✓ Thank you for contacting us! We\'ve received your message and will get back to you within 24 hours.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Show form errors."""
        messages.error(self.request, 'Please correct the errors below and try again.')
        return super().form_invalid(form)


class InquiryCreateView(LoginRequiredMixin, CreateView):
    """
    Create an inquiry about a property.
    User must be logged in but cannot inquire about own properties.
    """
    model = Inquiry
    form_class = InquiryForm
    template_name = 'messaging/inquiry_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Get property object early for validation."""
        try:
            self.house = Property.objects.get(slug=kwargs['slug'])
            # Permission check: cannot inquire about own property
            if self.house.owner == request.user:
                messages.error(request, 'You cannot inquire about your own property.')
                return redirect('listings:property_detail', slug=self.house.slug)
            # Check if property deal is done
            if self.house.deal_done:
                messages.error(request, 'This property is no longer available (deal done).')
                return redirect('listings:property_detail', slug=self.house.slug)
        except Property.DoesNotExist:
            messages.error(request, 'Property not found.')
            return redirect('listings:property_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add property to context."""
        context = super().get_context_data(**kwargs)
        context['property'] = self.house
        return context

    def form_valid(self, form):
        """
        Create inquiry or add to existing conversation.
        If an inquiry already exists between these users for this property,
        add the message to that conversation instead of creating a new inquiry.
        """
        message_text = form.cleaned_data['message']
        
        # Check if inquiry already exists
        existing_inquiry = Inquiry.objects.filter(
            house=self.house,
            from_user=self.request.user,
            to_user=self.house.owner
        ).first()
        
        if existing_inquiry:
            # Add message to existing conversation
            try:
                InquiryMessage.objects.create(
                    inquiry=existing_inquiry,
                    sender=self.request.user,
                    message=message_text,
                    is_read=False  # Receiver hasn't read the message yet
                )
                existing_inquiry.updated_at = timezone.now()
                # Sender is replying - receiver hasn't read the reply yet
                existing_inquiry.to_user_read = False
                existing_inquiry.save()
                messages.success(self.request, 'Your message has been sent! You can continue chatting in your inbox.')
                return redirect('listings:property_detail', slug=self.house.slug)
            except Exception as e:
                messages.error(self.request, f'Error sending message: {str(e)}')
                return self.form_invalid(form)
        else:
            # Create new inquiry
            inquiry = form.save(commit=False)
            inquiry.house = self.house
            inquiry.from_user = self.request.user
            inquiry.to_user = self.house.owner
            inquiry.to_user_read = False  # Receiver hasn't read it yet
            try:
                inquiry.save()
                messages.success(self.request, 'Your inquiry has been sent to the property owner! You can chat with them in your dashboard inbox.')
                return redirect('listings:property_detail', slug=self.house.slug)
            except Exception as e:
                messages.error(self.request, f'Error sending inquiry: {str(e)}')
                return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Rely on inline field errors only for reservation form."""
        return super().form_invalid(form)


class ReservationCreateView(LoginRequiredMixin, CreateView):
    """
    Create a reservation for a property.
    User must be logged in but cannot reserve own properties.
    """
    model = Reservation
    form_class = ReservationForm
    template_name = 'messaging/reservation_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Get property object early for validation."""
        try:
            self.house = Property.objects.get(slug=kwargs['slug'])
            # Check if property is marked as deal done
            if self.house.deal_done:
                messages.error(request, 'This property is no longer available (deal done).')
                return redirect('listings:property_detail', slug=self.house.slug)
            # Permission check: cannot reserve own property
            if self.house.owner == request.user:
                messages.error(request, 'You cannot reserve your own property.')
                return redirect('listings:property_detail', slug=self.house.slug)
            # Check if user already has an active reservation on this property
            existing_reservation = Reservation.objects.filter(
                house=self.house,
                from_user=request.user,
                status__in=['pending', 'confirmed']
            ).exists()
            if existing_reservation:
                messages.error(request, 'You already have an active reservation on this property. Please wait for the owner\'s response or cancel it.')
                return redirect('listings:property_detail', slug=self.house.slug)
        except Property.DoesNotExist:
            messages.error(request, 'Property not found.')
            return redirect('listings:property_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add property to context."""
        context = super().get_context_data(**kwargs)
        context['property'] = self.house
        return context

    def get_form_kwargs(self):
        """Pass property to form."""
        kwargs = super().get_form_kwargs()
        kwargs['property'] = self.house
        return kwargs

    def form_valid(self, form):
        """Set property and users before saving."""
        reservation = form.save(commit=False)
        reservation.house = self.house
        reservation.from_user = self.request.user
        reservation.to_user = self.house.owner
        try:
            reservation.save()
            messages.success(self.request, 'Your reservation request has been sent! The owner will review it shortly.')
            return redirect('listings:property_detail', slug=self.house.slug)
        except Exception as e:
            messages.error(self.request, f'Error creating reservation: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Rely on inline field errors only for reservation form."""
        return super().form_invalid(form)
