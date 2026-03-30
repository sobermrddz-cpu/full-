"""
Shared mixins for the application.
"""
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View


class OwnerRequiredMixin(LoginRequiredMixin):
    """
    Mixin to check if the current user is the owner of the object.
    Assumes the object has an 'owner' field pointing to the user.
    Raises Http404 if the user is not the owner.
    """

    def get_object(self, *args, **kwargs):
        """
        Get the object and check ownership.
        """
        obj = super().get_object(*args, **kwargs)

        # Check ownership
        if obj.owner != self.request.user:
            raise Http404("You don't have permission to access this resource.")

        return obj
