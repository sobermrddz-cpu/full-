from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    """Inline admin for PropertyImage."""
    model = PropertyImage
    extra = 1
    fields = ('image', 'is_primary', 'order')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin for Property model."""
    list_display = ('title', 'owner', 'property_type', 'city', 'price', 'status', 'deal_done_display', 'created_at', 'views_count')
    list_filter = ('status', 'deal_done', 'property_type', 'category', 'city', 'created_at', 'is_featured')
    search_fields = ('title', 'description', 'city', 'owner__username')
    readonly_fields = ('slug', 'views_count', 'created_at', 'updated_at', 'deal_confirmed_reservation')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyImageInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'owner', 'description')
        }),
        ('Property Details', {
            'fields': ('property_type', 'category', 'city', 'address', 'price')
        }),
        ('Physical Details', {
            'fields': ('area_sqm', 'rooms', 'bathrooms', 'floor')
        }),
        ('Features', {
            'fields': ('furnished', 'parking')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'deal_done', 'deal_confirmed_reservation')
        }),
        ('Engagement', {
            'fields': ('views_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['refuse_property']
    
    def refuse_property(self, request, queryset):
        """
        Admin action to refuse properties and delete their images.
        Images are deleted only if no other property is using them.
        """
        refused_count = 0
        images_deleted = 0
        
        for property_obj in queryset:
            # Get all images for this property
            images = property_obj.images.all()
            
            # Count images before deletion for reporting
            image_count = images.count()
            
            # Delete all PropertyImage records (cascade will delete images not used by other properties)
            images.delete()
            images_deleted += image_count
            
            # Mark property as refused
            property_obj.status = 'refused'
            property_obj.save()
            refused_count += 1
        
        # Show success message
        self.message_user(
            request,
            f'{refused_count} property(ies) marked as refused. {images_deleted} image(s) processed for deletion (kept shared images).',
            messages.SUCCESS
        )
    
    refuse_property.short_description = "Refuse selected properties and delete their images"
    
    def deal_done_display(self, obj):
        """Display deal_done status with visual indicator."""
        if obj.deal_done:
            return '✓ Deal Done'
        return '—'
    deal_done_display.short_description = 'Deal Status'


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    """Admin for PropertyImage model."""
    list_display = ('house', 'is_primary', 'order', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('house__title',)
    readonly_fields = ('uploaded_at',)
