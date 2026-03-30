from django.contrib import admin
from .models import ContactMessage, Inquiry, Reservation


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin for ContactMessage model."""
    list_display = ('subject', 'email', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Contact Info', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Admin for Inquiry model."""
    list_display = ('from_user', 'house', 'to_user_read', 'created_at')
    list_filter = ('to_user_read', 'created_at', 'house__category')
    search_fields = ('from_user__username', 'house__title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('house', 'from_user', 'to_user')
    fieldsets = (
        ('Inquiry Details', {
            'fields': ('house', 'from_user', 'to_user')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('to_user_read',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin for Reservation model."""
    list_display = ('id', 'from_user', 'house', 'check_in_date', 'check_out_date', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'check_in_date', 'house__category')
    search_fields = ('from_user__username', 'house__title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('house', 'from_user', 'to_user')
    fieldsets = (
        ('Reservation Details', {
            'fields': ('house', 'from_user', 'to_user')
        }),
        ('Dates', {
            'fields': ('check_in_date', 'check_out_date')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

