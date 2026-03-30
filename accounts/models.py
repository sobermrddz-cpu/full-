from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser.
    Adds phone, bio, and is_banned fields directly to the user model.
    """
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_banned = models.BooleanField(default=False, help_text='Banned users cannot login')

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.get_full_name() or self.username}'

    def get_full_name(self):
        """Returns the user's full name."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username
