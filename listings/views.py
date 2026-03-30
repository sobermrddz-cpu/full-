"""
Views for the listings app.
Handles property CRUD, search, filtering, and detail views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.http import Http404, HttpResponseForbidden
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator

from core.mixins import OwnerRequiredMixin
from .models import Property, PropertyImage
from .forms import PropertyForm, PropertyImageFormSet, PropertyFilterForm


class HomeView(TemplateView):
    """
    Home page with featured listings and hero section.
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        """Add featured properties to context."""
        context = super().get_context_data(**kwargs)
        # Get featured properties (max 3)
        featured = Property.objects.filter(
            status='active',
            is_featured=True
        ).select_related('owner').prefetch_related('images')[:3]
        
        # Get latest properties as fallback if no featured
        if not featured:
            featured = Property.objects.filter(
                status='active'
            ).select_related('owner').prefetch_related('images').order_by('-created_at')[:3]
        
        context['featured_properties'] = featured
        return context


class PropertyListView(ListView):
    """
    List all active properties with search and filtering.
    Paginated at 12 listings per page.
    """
    model = Property
    template_name = 'listings/property_list.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        """
        Filter and search properties based on GET parameters.
        Excludes properties with deal_done status.
        """
        queryset = Property.objects.filter(status='active', deal_done=False).select_related('owner').prefetch_related('images')

        # Search - case-insensitive, partial match allowed
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            # Search in title, description, city, and address (case-insensitive, partial match)
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        else:
            queryset = queryset.order_by('-created_at')

        # Filters
        property_types = self.request.GET.getlist('property_type')
        if property_types:
            queryset = queryset.filter(property_type__in=property_types)

        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category__in=categories)

        city = self.request.GET.get('city', '').strip()
        if city:
            queryset = queryset.filter(city__icontains=city)

        min_price = self.request.GET.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        min_rooms = self.request.GET.get('min_rooms')
        if min_rooms:
            try:
                queryset = queryset.filter(rooms__gte=int(min_rooms))
            except ValueError:
                pass

        furnished = self.request.GET.get('furnished')
        if furnished in ['true', 'false']:
            queryset = queryset.filter(furnished=furnished == 'true')

        parking = self.request.GET.get('parking')
        if parking in ['true', 'false']:
            queryset = queryset.filter(parking=parking == 'true')

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['-created_at', 'price', '-price', '-views_count']:
            queryset = queryset.order_by(sort) if not search_query else queryset

        return queryset

    def get_context_data(self, **kwargs):
        """Add filter form to context."""
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PropertyFilterForm(self.request.GET)
        context['query_string'] = self.request.GET.urlencode()
        return context


class PropertyDetailView(DetailView):
    """
    Display property details with images and inquiry/reservation forms.
    Increments views_count on each GET.
    """
    model = Property
    template_name = 'listings/property_detail.html'
    context_object_name = 'property'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Only show active and deleted properties (but not really deleted)."""
        return Property.objects.select_related('owner').prefetch_related('images').exclude(status='deleted')

    def get(self, request, *args, **kwargs):
        """Increment views_count only for unique users."""
        response = super().get(request, *args, **kwargs)
        
        # Only count views from authenticated users
        if request.user.is_authenticated:
            property_obj = self.object
            # Check if user has already viewed this property
            if not property_obj.viewed_by.filter(pk=request.user.pk).exists():
                # Add user to viewed_by and increment counter
                property_obj.viewed_by.add(request.user)
                Property.objects.filter(pk=property_obj.pk).update(views_count=F('views_count') + 1)
        
        return response

    def get_context_data(self, **kwargs):
        """Add owner check and message forms to context."""
        context = super().get_context_data(**kwargs)
        context['is_owner'] = self.object.owner == self.request.user
        
        # Get similar properties but exclude current property and user's own properties
        related_properties = Property.objects.filter(
            category=self.object.category,
            status='active'
        ).exclude(pk=self.object.pk)
        
        # Exclude properties owned by current user if authenticated
        if self.request.user.is_authenticated:
            related_properties = related_properties.exclude(owner=self.request.user)
        
        context['related_properties'] = related_properties.select_related('owner')[:2]
        return context


class PropertyCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new property listing.
    Handles multiple image uploads.
    """
    model = Property
    form_class = PropertyForm
    template_name = 'listings/property_form.html'
    success_url = reverse_lazy('dashboard:overview')

    def get_context_data(self, **kwargs):
        """Add formset to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PropertyImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = PropertyImageFormSet(instance=self.object)
        context['title'] = 'Create New Listing'
        context['button_text'] = 'Create Listing'
        return context

    def form_valid(self, form):
        """
        Save property first, then save images with the property instance.
        Even if image formset is invalid, don't block property creation.
        Staff/admin properties are created as 'active', regular users as 'pending'.
        """
        # Save the core property first
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        # Admin/staff properties are auto-approved, regular users need approval
        self.object.status = 'active' if self.request.user.is_staff else 'pending'
        self.object.save()

        # Now create and save the formset with the saved property instance
        formset = PropertyImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        
        # Try to save images, but don't block on errors
        if formset.is_valid():
            # Save formset, which automatically skips empty forms
            formset.save()
        else:
            # Log formset errors for debugging
            print(f"Formset errors: {formset.errors}")
            print(f"Formset non-form errors: {formset.non_form_errors()}")

        # Show different message based on user type
        if self.request.user.is_staff:
            messages.success(self.request, 'Property posted successfully!')
        else:
            messages.success(self.request, 'Property listing created successfully! Pending admin approval.')
        return redirect(self.success_url)


class PropertyEditView(OwnerRequiredMixin, UpdateView):
    """
    Edit an existing property listing.
    Only the owner can edit.
    """
    model = Property
    form_class = PropertyForm
    template_name = 'listings/property_form.html'
    success_url = reverse_lazy('dashboard:overview')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Get property for editing."""
        return Property.objects.exclude(status='deleted')

    def get_context_data(self, **kwargs):
        """Add formset to context."""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PropertyImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = PropertyImageFormSet(instance=self.object)
        context['title'] = 'Edit Listing'
        context['button_text'] = 'Update Listing'
        return context

    def form_valid(self, form):
        """
        Save property first, then save images.
        If new images are added, reset property status to 'pending' for admin review.
        Don't prevent updates if image formset has issues.
        """
        # Save the main property data
        self.object = form.save()

        # Create and save the formset with the saved property instance
        formset = PropertyImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        
        # Check if new images were added
        new_images_added = False
        
        # Try to save images, but don't block on errors
        if formset.is_valid():
            # Check if any new images are being added
            for form_item in formset.forms:
                if form_item.cleaned_data:
                    # Check if new image file is being uploaded (only for new instances)
                    if form_item.cleaned_data.get('image') and not form_item.instance.id:
                        new_images_added = True
                        break
            
            # Save formset
            formset.save()
            
            # If new images were added and property is active, reset to pending for admin review (but NOT for admin users)
            if new_images_added and self.object.status == 'active' and not self.request.user.is_staff:
                self.object.status = 'pending'
                self.object.save(update_fields=['status', 'updated_at'])
                messages.success(self.request, 'Property listing updated. Admin review required due to new images.')
            else:
                messages.success(self.request, 'Property listing updated successfully!')
        else:
            # Log formset errors for debugging
            print(f"Formset errors: {formset.errors}")
            print(f"Formset non-form errors: {formset.non_form_errors()}")
            messages.success(self.request, 'Property listing updated (image update had issues).')

        return redirect(self.success_url)


class PropertyDeleteView(OwnerRequiredMixin, DeleteView):
    """
    Delete (soft delete) a property listing.
    Only the owner can delete.
    Sets status to 'deleted' instead of hard deleting.
    """
    model = Property
    template_name = 'listings/property_confirm_delete.html'
    success_url = reverse_lazy('dashboard:overview')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Only show non-deleted properties."""
        return Property.objects.exclude(status='deleted')

    def delete(self, request, *args, **kwargs):
        """Soft delete by setting status to 'deleted'."""
        self.object = self.get_object()
        self.object.status = 'deleted'
        self.object.save()
        messages.success(request, 'Property listing has been deleted.')
        return redirect(self.success_url)
