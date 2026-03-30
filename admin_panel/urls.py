"""
URL configuration for the admin_panel app.
"""
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminPanelOverviewView.as_view(), name='overview'),
    path('listings/', views.ListingsManagerView.as_view(), name='listings'),
    path('listings/<int:pk>/approve/', views.PropertyApproveView.as_view(), name='listing_approve'),
    path('listings/<int:pk>/reject/', views.PropertyRejectView.as_view(), name='listing_reject'),
    path('users/', views.UsersManagerView.as_view(), name='users'),
    path('users/<int:pk>/ban/', views.UserBanToggleView.as_view(), name='user_ban_toggle'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('contacts/', views.ContactsInboxView.as_view(), name='contacts'),
    path('contacts/<int:pk>/delete/', views.ContactMessageDeleteView.as_view(), name='contact_delete'),
]
