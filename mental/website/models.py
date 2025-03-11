from django.db import models
from django.contrib.auth.models import User
from textblob import TextBlob 
import random

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

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        (1, 'Very Sad'),
        (2, 'Sad'),
        (3, 'Neutral'),
        (4, 'Happy'),
        (5, 'Very Happy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood_score = models.IntegerField(choices=MOOD_CHOICES, default=3)
    description = models.TextField(blank=True, null=True)  # Optional mood description
    sentiment_score = models.FloatField(default=0.0)  # Sentiment Analysis Score
    date = models.DateTimeField(auto_now_add=True)

    def analyze_sentiment(self):
        if self.description:
            analysis = TextBlob(self.description)
            return analysis.sentiment.polarity  # Ranges from -1 (negative) to 1 (positive)
        return 0.0  # Default for no description

    def save(self, *args, **kwargs):
        self.sentiment_score = self.analyze_sentiment()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_mood_score_display()} ({self.date})"

