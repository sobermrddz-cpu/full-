from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import CustomUser
from listings.models import Property


class ContactMessage(models.Model):
    """
    General contact form messages from website visitors.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f'{self.subject} - {self.email}'


class Inquiry(models.Model):
    """
    Inquiry from a user about a property.
    Connects interested buyers/renters with property owners.
    """
    house = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='inquiries'
    )
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_inquiries'
    )
    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_inquiries'
    )
    message = models.TextField()
    # Read status for the receiver (property owner)
    # to_user_read = has the receiver read the initial inquiry?
    to_user_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Property Inquiry'
        verbose_name_plural = 'Property Inquiries'
        indexes = [
            models.Index(fields=['to_user', '-created_at']),
            models.Index(fields=['to_user', 'to_user_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        if not self.from_user_id or not self.house_id:
            return 'Inquiry (unspecified sender/property)'
        return f'Inquiry from {self.from_user.get_full_name()} about {self.house.title}'

    def clean(self):
        """Validate inquiry."""
        # Skip validation until required relationships are set by the view
        if not self.from_user_id or not self.to_user_id or not self.house_id:
            return
        # Prevent inquiries to self
        if self.from_user == self.to_user:
            raise ValidationError('You cannot send an inquiry about your own property.')
        
        # Ensure to_user is the property owner
        if self.to_user != self.house.owner:
            raise ValidationError('Inquiry recipient must be the property owner.')

    def save(self, *args, **kwargs):
        """Save inquiry with validation."""
        if not self.to_user_id:
            self.to_user = self.house.owner
        self.clean()
        super().save(*args, **kwargs)


class InquiryMessage(models.Model):
    """
    Chat message within an inquiry thread.
    Allows back-and-forth communication between buyer and seller.
    """
    inquiry = models.ForeignKey(
        Inquiry,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='inquiry_messages_sent'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # Has the receiver read this message?
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Inquiry Message'
        verbose_name_plural = 'Inquiry Messages'
        indexes = [
            models.Index(fields=['inquiry', 'created_at']),
        ]

    def __str__(self):
        return f'Message from {self.sender.get_full_name()} in Inquiry {self.inquiry.id}'


class Reservation(models.Model):
    """
    Reservation/booking for a property.
    Used for vacation rentals, short-term rentals, etc.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    house = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_reservations'
    )
    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_reservations'
    )
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    deleted_for_guest_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Timestamp when guest deleted from their dashboard (soft delete)')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'
        indexes = [
            models.Index(fields=['house', 'check_in_date', 'check_out_date']),
            models.Index(fields=['to_user', '-created_at']),
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Reservation {self.id} - {self.house.title} ({self.status})'

    def clean(self):
        """Validate reservation."""
        # Skip validation until required relationships are set by the view
        if not self.from_user_id or not self.to_user_id or not self.house_id:
            return
        # Prevent reservations to self
        if self.from_user == self.to_user:
            raise ValidationError('You cannot reserve your own property.')
        
        # Ensure to_user is the property owner
        if self.to_user != self.house.owner:
            raise ValidationError('Reservation must be for the property owner.')
        
        # Sale properties require only meeting date (check_in_date).
        if self.house.property_type == 'sale':
            if not self.check_in_date:
                raise ValidationError('Meeting date is required for sale properties.')
            self.check_out_date = None
            if self.check_in_date < timezone.now().date():
                raise ValidationError('Meeting date cannot be in the past.')
            return

        # Rent/vacation reservations require both dates.
        if not self.check_in_date or not self.check_out_date:
            raise ValidationError('Check-in and check-out dates are required.')

        # Ensure check_out_date is after check_in_date
        if self.check_out_date <= self.check_in_date:
            raise ValidationError('Check-out date must be after check-in date.')
        
        # Ensure check-in date is not in the past
        if self.check_in_date < timezone.now().date():
            raise ValidationError('Check-in date cannot be in the past.')

    def save(self, *args, **kwargs):
        """Save reservation with validation."""
        if not self.to_user_id:
            self.to_user = self.house.owner
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration_days(self):
        """Get duration in days. Returns None if dates are not set."""
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return None

    @property
    def estimated_total(self):
        """Get estimated total cost for rent/vacation properties. Returns None for other types."""
        if self.house.property_type in ['rent', 'vacation'] and self.duration_days:
            return self.duration_days * self.house.price
        return None

    def get_status_display_html(self):
        """Get HTML badge for reservation status."""
        colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary',
        }
        color = colors.get(self.status, 'secondary')
        badge_text = self.get_status_display()
        return f'<span class="badge bg-{color}">{badge_text}</span>'

