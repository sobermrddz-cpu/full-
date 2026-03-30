from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os

User = get_user_model()

# Property type and category choices
PROPERTY_TYPE_CHOICES = [
    ('sale', 'For Sale'),
    ('rent', 'For Rent'),
    ('vacation', 'Vacation Rental'),
]

PROPERTY_CATEGORY_CHOICES = [
    ('apartment', 'Apartment'),
    ('villa', 'Villa'),
    ('land', 'Land'),
    ('commercial', 'Commercial'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('active', 'Active'),
    ('reserved', 'Reserved'),
    ('sold', 'Sold'),
    ('rented', 'Rented'),
    ('refused', 'Refused'),
    ('deleted', 'Deleted'),
]


class Property(models.Model):
    """
    Real estate property listing model.
    Includes all property details and soft delete functionality.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Property details
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=PROPERTY_CATEGORY_CHOICES)
    city = models.CharField(max_length=100, db_index=True)
    address = models.CharField(max_length=255)
    
    # Physical details
    area_sqm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    rooms = models.SmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    bathrooms = models.SmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    floor = models.SmallIntegerField(null=True, blank=True)  # 0 = ground floor
    
    # Features
    furnished = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    is_featured = models.BooleanField(default=False)
    deal_done = models.BooleanField(default=False, db_index=True)  # Marks if reservation is confirmed/deal closed
    deal_confirmed_reservation = models.ForeignKey('messaging.Reservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='property_deal_closed')
    
    # Engagement tracking
    views_count = models.IntegerField(default=0)
    viewed_by = models.ManyToManyField(User, related_name='viewed_properties', blank=True)
    
    # Owner
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    
    # Full-text search (PostgreSQL)
    search_vector = SearchVectorField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['status']),
            models.Index(fields=['property_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from title on both create and update.
        If slug conflicts, append number suffix (-2, -3, etc).
        Only regenerates slug if title has changed or slug is missing.
        """
        # Check if this is an update and if title has changed
        if self.pk:
            # This is an update - check if title changed
            try:
                old_instance = Property.objects.get(pk=self.pk)
                title_changed = old_instance.title != self.title
            except Property.DoesNotExist:
                title_changed = True
        else:
            # This is a new instance
            title_changed = True
        
        # Generate slug only if it's missing or title has changed
        if not self.slug or title_changed:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 2

            # Handle slug conflicts (exclude current property)
            while Property.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        """Get the primary image for this property."""
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def is_available(self):
        """Check if property is available for viewing."""
        return self.status == 'active'

    def get_status_display_html(self):
        """Get HTML badge for property status."""
        colors = {
            'pending': 'warning',
            'active': 'success',
            'sold': 'danger',
            'rented': 'info',
            'deleted': 'secondary',
        }
        badge_class = colors.get(self.status, 'secondary')
        return f'<span class="badge bg-{badge_class}">{self.get_status_display()}</span>'

    def get_absolute_url(self):
        """Get absolute URL for this property."""
        from django.urls import reverse
        return reverse('listings:property_detail', kwargs={'slug': self.slug})


class PropertyImage(models.Model):
    """
    Property image model.
    Supports multiple images per property with ordering.
    """
    house = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/', blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.SmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f'{self.house.title} - Image {self.order + 1}'

    def clean(self):
        """Validate image file."""
        if self.image:
            # Check file size (max 10MB)
            file_size = self.image.size
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('Image size must not exceed 10MB.')

            # Check MIME type (skip if python-magic not installed)
            try:
                import magic
                mime = magic.Magic(mime=True)
                file_mime = mime.from_buffer(self.image.read())
                self.image.seek(0)

                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if file_mime not in allowed_types:
                    raise ValidationError('Only JPG, PNG, GIF and WebP images are allowed.')
            except (ImportError, OSError):
                # python-magic not available or MIME check failed, skip
                pass

    def save(self, *args, **kwargs):
        """
        Ensure only one primary image per property.
        """
        self.clean()

        if self.is_primary:
            # Remove primary flag from other images
            PropertyImage.objects.filter(house=self.house).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

    @property
    def image_url(self):
        """Get image URL."""
        return self.image.url if self.image else None

    def delete(self, *args, **kwargs):
        """
        Delete the image file from storage only if no other PropertyImage uses it.
        This prevents deleting shared images when one property is deleted.
        """
        image_path = self.image.name if self.image else None
        
        # Delete the database record first
        super().delete(*args, **kwargs)
        
        # Only delete the file if no other PropertyImage references it
        if image_path:
            # Check if any other PropertyImage still uses this file
            other_images = PropertyImage.objects.filter(image=image_path).exists()
            
            if not other_images:
                # Safe to delete - no other property uses this image
                storage = self.image.storage
                if storage.exists(image_path):
                    storage.delete(image_path)


# Signal handlers for file cleanup
@receiver(pre_delete, sender=PropertyImage)
def delete_property_image_file(sender, instance, **kwargs):
    """
    Signal handler to delete image files when PropertyImage is bulk-deleted.
    Only deletes the file if no other PropertyImage is using it.
    
    This handles edge cases where delete() is overridden or bulk QuerySet.delete() is used.
    """
    image_path = instance.image.name if instance.image else None
    
    if image_path:
        # Check if any other PropertyImage still uses this file (after this one is deleted)
        other_images = PropertyImage.objects.filter(image=image_path).exclude(pk=instance.pk).exists()
        
        if not other_images:
            # Safe to delete - no other property uses this image
            storage = instance.image.storage
            if storage.exists(image_path):
                storage.delete(image_path)
