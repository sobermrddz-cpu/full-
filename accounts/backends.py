from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that supports login with username or email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by username or email with password.
        """
        try:
            # Try to get user by username or email
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                # If not found by username, try by email
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        # Check if user is banned
        if user.is_banned:
            return None

        # Verify password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """
        Get user by ID.
        Return None if user is banned (to invalidate existing sessions).
        """
        try:
            user = User.objects.get(pk=user_id)
            # Return None if user is banned to log them out
            if user.is_banned:
                return None
            return user
        except User.DoesNotExist:
            return None
