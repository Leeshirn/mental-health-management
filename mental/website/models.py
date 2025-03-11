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



class JournalSettings(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    custom_interval_days = models.PositiveIntegerField(blank=True, null=True)  # For custom option
    
    def __str__(self):
        return f"{self.user.username}'s Journal Settings"

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    sentiment_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def analyze_sentiment(self):
        if self.content:
            analysis = TextBlob(self.content)
            return analysis.sentiment.polarity
        return 0.0

    def save(self, *args, **kwargs):
        self.sentiment_score = self.analyze_sentiment()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.created_at})"

class JournalPrompt(models.Model):
    text = models.TextField(unique=True)
    
    def __str__(self):
        return self.text[:50]  # Show a preview of the prompt

    @staticmethod
    def get_random_prompt():
        prompt = JournalPrompt.objects.order_by('?').first()
        return prompt.text if prompt else "Write about anything that's on your mind."

# Predefined list of mental health prompts for initial population
def populate_prompts():
    prompts = [
        "What would you do with a one-year sabbatical?",
        "What does it look like when you're operating at your best?",
        "What is one of the wisest decisions you made?",
        "Write about someone or something that has inspired you recently.",
        "List five things you are grateful for.",
        "What is your vision for what you hope to achieve through your work?"
    ]
    for prompt_text in prompts:
        JournalPrompt.objects.get_or_create(text=prompt_text)
