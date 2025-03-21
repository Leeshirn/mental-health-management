from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile
from .models import MoodEntry, JournalEntry, JournalSettings

class SignUpForm(UserCreationForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('professional', 'Professional'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Register as")
     
    # Only required for professionals
    license_number = forms.CharField(
        max_length=20, 
        required=False,  
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'License Number (Professionals Only)'}),
    )
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help text for username, password1, and password2
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        license_number = cleaned_data.get('license_number')

        if role == 'professional' and not license_number:
            raise forms.ValidationError("License number is required for professionals.")
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        license_number = self.cleaned_data.get('license_number')

        if commit:
            user.save()
            is_verified = False if role == 'professional' else True  # Professionals need verification
            UserProfile.objects.create(user=user, role=role, license_number=license_number, is_verified=is_verified)
        return user


class MoodEntryForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood', 'description']
        widgets = {
             'description': forms.Textarea(attrs={
                'rows': 3,  # Number of visible rows (adjust as needed)
                'cols': 40,  # Number of visible columns (adjust as needed)
                'style': 'resize: none; width: 100%; max-width: 500px;',  # Disable resizing and set width
                'class': 'form-control',
            }),
        }


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['title', 'content']
        

class JournalSettingsForm(forms.ModelForm):
    class Meta:
        model = JournalSettings
        fields = ['frequency', 'custom_interval_days']
