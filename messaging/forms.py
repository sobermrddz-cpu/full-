from django import forms
from django.forms import ModelForm
from .models import ContactMessage, Inquiry, Reservation, InquiryMessage


class ContactForm(forms.ModelForm):
    """Form for general contact messages."""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (Optional)'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your Message',
                'rows': 5,
                'required': True
            }),
        }


class InquiryForm(forms.ModelForm):
    """Form for property inquiries."""
    
    class Meta:
        model = Inquiry
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell the owner why you\'re interested...',
                'rows': 4,
            }),
        }
    
    def clean_message(self):
        """Validate message is not empty."""
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError('Message cannot be empty.')
        if len(message) < 5:
            raise forms.ValidationError('Message must be at least 5 characters long.')
        return message


class ReservationForm(forms.ModelForm):
    """Form for property reservations."""
    
    class Meta:
        model = Reservation
        fields = ['check_in_date', 'check_out_date', 'message']
        widgets = {
            'check_in_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'check_out_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Any special requests? (Optional)',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, property=None, **kwargs):
        """Set date requirements based on property type."""
        super().__init__(*args, **kwargs)
        self.property = property

        # Sale properties use only a meeting date (check_in_date).
        if property and property.property_type == 'sale':
            self.fields['check_out_date'].required = False
    
    def clean(self):
        """Validate reservation dates according to property type."""
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        property_type = getattr(self.property, 'property_type', None)

        if not check_in:
            self.add_error('check_in_date', 'Please select a check-in date.')

        # Rent/vacation reservations require a checkout date too.
        if property_type in ['rent', 'vacation']:
            if not check_out:
                self.add_error('check_out_date', 'Please select a check-out date.')

        # For sale reservations, ignore checkout even if browser sends one.
        if property_type == 'sale':
            cleaned_data['check_out_date'] = None
            return cleaned_data

        # Date order/past validations for rental-like reservations.
        if check_in and check_out:
            from datetime import date
            today = date.today()
            if check_in < today:
                self.add_error('check_in_date', 'Check-in date cannot be in the past.')
            if check_out <= check_in:
                self.add_error('check_out_date', 'Check-out date must be after check-in date.')
        
        return cleaned_data

class InquiryMessageForm(forms.ModelForm):
    """Form for sending messages in inquiry chat."""
    
    class Meta:
        model = InquiryMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Type your message...',
                'rows': 3,
            }),
        }
    
    def clean_message(self):
        """Validate message is not empty."""
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError('Message cannot be empty.')
        return message
