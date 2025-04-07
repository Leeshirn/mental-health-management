from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
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


class MentalHealthProfessional(models.Model):
    PROFESSION_CHOICES = [
        ('PSY', 'Psychiatrist'),
        ('CLP', 'Clinical Psychologist'),
        ('CP', 'Counseling Psychologist'),
        ('SW', 'Clinical Social Worker'),
        ('MFT', 'Marriage & Family Therapist'),
        ('LPC', 'Licensed Professional Counselor'),
        ('ART', 'Art Therapist'),
        ('MHC', 'Mental Health Counselor'),
    ]

    APPROACH_CHOICES = [
        ('CBT', 'Cognitive Behavioral Therapy'),
        ('PDY', 'Psychodynamic Therapy'),
        ('HMN', 'Humanistic Therapy'),
        ('INT', 'Integrative Therapy'),
        ('DBT', 'Dialectical Behavior Therapy'),
        ('ACT', 'Acceptance & Commitment Therapy'),
        ('EMD', 'EMDR'),
        ('SOL', 'Solution-Focused Therapy'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mental_health_pro')
    profession = models.CharField(max_length=3, choices=PROFESSION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    license_state = models.CharField(max_length=50)
    therapeutic_approaches = models.CharField(max_length=200)  # Comma-separated list of APPROACH_CHOICES
    bio = models.TextField(blank=True)
    profile_complete = models.BooleanField(default=False)
    
    # Professional Details
    years_of_experience = models.PositiveIntegerField(default=0)
    qualifications = models.TextField()
    areas_of_focus = models.TextField(help_text="Specific mental health conditions or populations you specialize in")
    
    # Practice Information
    practice_name = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    accepts_insurance = models.BooleanField(default=False)
    sliding_scale = models.BooleanField(default=False)
    
    # Contact Information
    phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = CountryField()
    postal_code = models.CharField(max_length=20)
    
    # Session Details
    session_format = models.CharField(max_length=100, 
                                   choices=[('INP', 'In-person'), ('ONL', 'Online'), ('BOTH', 'Both')])
    session_length = models.PositiveIntegerField(default=50, help_text="Typical session length in minutes")
    session_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00,  # Add default value
        help_text="Fee per session in your local currency")
    
    # Availability
    availability = models.TextField(help_text="Your typical availability (e.g., Mon-Wed 9am-5pm)")
    
    # Media
    profile_picture = models.ImageField(upload_to='therapists/profile_pics/', blank=True)
    license_verification = models.FileField(upload_to='therapists/license_docs/')
    
    # Emergency Protocols
    crisis_protocol = models.TextField(blank=True, help_text="Your protocol for handling client crises")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_profession_display()}"

    def get_approaches_list(self):
        return [dict(self.APPROACH_CHOICES).get(code, code) 
                for code in self.therapeutic_approaches.split(',')]