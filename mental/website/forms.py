from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile
from .models import MoodEntry, JournalEntry, JournalSettings,  MentalHealthProfessional, PatientProfile, Availability,PatientProfessionalRelationship, Note
from django.core.validators import MinValueValidator

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



class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = [ 'age', 'gender', 'phone', 'email', 'bio', 'profile_picture']


class MentalHealthProfessionalForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    therapeutic_approaches = forms.MultipleChoiceField(
        choices=MentalHealthProfessional.APPROACH_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = MentalHealthProfessional
        fields = [
            'first_name', 'last_name', 'email',
            'profession', 'license_number', 'license_state',
            'therapeutic_approaches', 'bio',
            'years_of_experience', 'qualifications', 'areas_of_focus',
            'practice_name', 'website', 'accepts_insurance', 'sliding_scale',
            'phone', 'emergency_contact', 'address', 'city', 
            'state', 'country', 'postal_code',
            'session_format', 'session_length', 'session_fee',
            'availability', 'profile_picture', 'license_verification',
            'crisis_protocol'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Your professional background and philosophy'}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
            'areas_of_focus': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g., Anxiety, Depression, LGBTQ+ issues, Trauma'
            }),
            'availability': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'e.g., Monday-Thursday 9am-7pm, Friday 9am-3pm'
            }),
            'crisis_protocol': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe how you handle emergency situations'
            }),
        }
        help_texts = {
            'session_fee': 'Your standard fee per session',
            'sliding_scale': 'Do you offer sliding scale fees based on income?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            if self.instance.therapeutic_approaches:
                self.fields['therapeutic_approaches'].initial = self.instance.therapeutic_approaches.split(',')
    
    def clean_therapeutic_approaches(self):
        approaches = self.cleaned_data.get('therapeutic_approaches')
        return ','.join(approaches)
    
    def save(self, commit=True):
        professional = super().save(commit=False)
        
        # Update User model fields
        user = professional.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            professional.profile_complete = True
            professional.save()
        
        return professional
    

class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class PatientConsentForm(forms.ModelForm):
    class Meta:
        model = PatientProfessionalRelationship
        fields = ['access_mood', 'access_journal', 'journal_access_level']
        widgets = {
            'journal_access_level': forms.RadioSelect
        }
        
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write a note about this session...'
            })
        }
        labels = {
            'content': ''
        }