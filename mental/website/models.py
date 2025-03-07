from django.db import models
from django.contrib.auth.models import User

# Create your models here.
ROLE_CHOICES = [
    ('donor', 'Donor'),
    ('recipient', 'Recipient'),
    ('agent', 'Agent'),
    ]
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices = ROLE_CHOICES, default='donor')
    created_at = models.DateTimeField(auto_now_add=True)
     
    def __str__(self):
        return (f"{self.user.username}'s Profile")