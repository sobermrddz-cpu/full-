"""
Forms for the listings app.
"""
from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from .models import Property, PropertyImage


class PropertyForm(forms.ModelForm):
    """
    Form for creating/editing property listings.
    """
    class Meta:
        model = Property
        fields = (
            'title', 'description', 'price',
            'property_type', 'category', 'city', 'address',
            'area_sqm', 'rooms', 'bathrooms', 'floor',
            'furnished', 'parking'
        )
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Beautiful 3-bedroom apartment in Algiers'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your property in detail',
                'rows': 6
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price in DZD'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Algiers, Oran, Constantine'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full address'
            }),
            'area_sqm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Area in m²'
            }),
            'rooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of rooms'
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of bathrooms'
            }),
            'floor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Floor number (0 = ground floor)'
            }),
            'furnished': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'parking': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class PropertyImageForm(forms.ModelForm):
    """
    Form for uploading property images.
    Image field is optional to allow empty formset rows and image updates.
    """
    image = forms.ImageField(required=False)
    order = forms.IntegerField(required=False, initial=0, widget=forms.HiddenInput())
    
    class Meta:
        model = PropertyImage
        fields = ('image', 'is_primary', 'order')
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.HiddenInput(),
        }
    
    def save(self, commit=True):
        """
        Skip saving if no image is provided AND instance is new (empty form).
        Allow deletion via DELETE checkbox (handled by formset).
        Allow metadata updates even without new image.
        """
        # If no image is provided AND this is a new instance, skip it
        if not self.cleaned_data.get('image') and not self.instance.pk:
            return None
        return super().save(commit=commit)


# Formset for managing multiple images
PropertyImageFormSet = inlineformset_factory(
    Property,
    PropertyImage,
    form=PropertyImageForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class PropertyFilterForm(forms.Form):
    """
    Form for filtering and searching properties.
    """
    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('-views_count', 'Most Viewed'),
    ]

    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, description...'
        })
    )
    
    property_type = forms.MultipleChoiceField(
        label='Property Type',
        required=False,
        choices=Property._meta.get_field('property_type').choices,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    category = forms.MultipleChoiceField(
        label='Category',
        required=False,
        choices=Property._meta.get_field('category').choices,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    city = forms.CharField(
        label='City',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Algiers'
        })
    )
    
    min_price = forms.DecimalField(
        label='Min Price (DZD)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum price'
        })
    )
    
    max_price = forms.DecimalField(
        label='Max Price (DZD)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum price'
        })
    )
    
    min_rooms = forms.IntegerField(
        label='Min Rooms',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum rooms'
        })
    )
    
    furnished = forms.NullBooleanField(
        label='Furnished',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }, choices=[
            ('', 'Any'),
            (True, 'Furnished'),
            (False, 'Unfurnished'),
        ])
    )
    
    parking = forms.NullBooleanField(
        label='Parking',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }, choices=[
            ('', 'Any'),
            (True, 'With Parking'),
            (False, 'Without Parking'),
        ])
    )
    
    sort = forms.ChoiceField(
        label='Sort By',
        required=False,
        choices=SORT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
