from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('patient', 'Patient'),
    ('professional', 'Professional'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)  # Only applies to professionals

    def __str__(self):
        return f"{self.user.username} ({self.role})"
