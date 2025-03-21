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


# Mood categories
MOOD_CATEGORIES = [
    ('Positive', 'Positive'),
    ('Negative', 'Negative'),
    ('Neutral', 'Neutral'),
]

# Mood choices with scores
MOODS = [
    ('happy', 'Positive', 10),
    ('excited', 'Positive', 9),
    ('grateful', 'Positive', 9),
    ('content', 'Positive', 8),
    ('hopeful', 'Positive', 8),
    ('proud', 'Positive', 7),
    ('relaxed', 'Positive', 7),
    ('loved', 'Positive', 9),
    ('confident', 'Positive', 8),
    ('energetic', 'Positive', 8),
    ('optimistic', 'Positive', 9),
    ('relieved', 'Positive', 8),
    ('calm', 'Neutral', 4),
    ('bored', 'Neutral', 2),
    ('indifferent', 'Neutral', 1),
    ('tired', 'Negative', -1),
    ('okay', 'Neutral', 3),
    ('apathetic', 'Negative', -1),
    ('unsure', 'Neutral', 2),
    ('blank', 'Neutral', 0),
    ('sad', 'Negative', -2),
    ('angry', 'Negative', -4),
    ('stressed', 'Negative', -4),
    ('frustrated', 'Negative', -3),
    ('anxious', 'Negative', -5),
    ('guilty', 'Negative', -3),
    ('lonely', 'Negative', -4),
    ('hopeless', 'Negative', -5),
    ('overwhelmed', 'Negative', -5),
    ('disappointed', 'Negative', -3),
]

class MoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=50, choices=[(m[0], m[0]) for m in MOODS])
    category = models.CharField(max_length=10, choices=MOOD_CATEGORIES, default='Neutral')
    score = models.IntegerField(default = 1)
    description = models.TextField(blank=True, null=True)
    date_logged = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically assign category and score based on mood
        for mood_name, category, score in MOODS:
            if self.mood == mood_name:
                self.category = category
                self.score = score
                break
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.mood} ({self.date_logged.strftime('%Y-%m-%d %H:%M:%S')})"


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
