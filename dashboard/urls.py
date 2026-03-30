"""
URL configuration for the dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardOverviewView.as_view(), name='overview'),
    path('listings/', views.MyListingsView.as_view(), name='listings'),
    path('inbox/', views.MyInboxView.as_view(), name='inbox'),
    path('inbox/<int:inquiry_id>/delete/', views.delete_inquiry, name='delete_inquiry'),
    path('reservations/', views.MyReservationsView.as_view(), name='reservations'),
    path('reservations/<int:reservation_id>/<str:action>/', views.reservation_action, name='reservation_action'),
]
