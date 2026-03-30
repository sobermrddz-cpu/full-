"""
URL configuration for the messaging app.
"""
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('contact/', views.ContactFormView.as_view(), name='contact'),
    path('listings/<slug:slug>/inquiry/', views.InquiryCreateView.as_view(), name='inquiry_create'),
    path('listings/<slug:slug>/reserve/', views.ReservationCreateView.as_view(), name='reservation_create'),
]
