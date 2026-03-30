"""
URL configuration for the listings app.
"""
from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    # Home page
    path('', views.HomeView.as_view(), name='home'),

    # Property listing URLs
    path('listings/', views.PropertyListView.as_view(), name='property_list'),
    # Important: more specific paths BEFORE the slug catch-all
    path('listings/new/', views.PropertyCreateView.as_view(), name='property_new'),
    path('listings/<slug:slug>/edit/', views.PropertyEditView.as_view(), name='property_edit'),
    path('listings/<slug:slug>/delete/', views.PropertyDeleteView.as_view(), name='property_delete'),
    path('listings/<slug:slug>/', views.PropertyDetailView.as_view(), name='property_detail'),
]
