from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # App URLs (listings includes home at /)
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', include(('listings.urls', 'listings'), namespace='listings')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('admin-panel/', include(('admin_panel.urls', 'admin_panel'), namespace='admin_panel')),
    path('', include(('messaging.urls', 'messaging'), namespace='messaging')),

    # Static pages
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

