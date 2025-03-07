from django.contrib.auth.forms import UserCreationForm 
from django.contrib.auth.models import User 
from django import forms
from .models import UserProfile


class SignUpForm(UserCreationForm):
   email = forms.EmailField(label="", widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
   first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'First Name'}))
   last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
   ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('professional', 'Professional'),
        ('administrator', 'Administator'),
    ]
   role = forms.ChoiceField(choices=ROLE_CHOICES, label="Register as")
  
   class Meta:
      model = User
      fields = ('username', 'password1', 'password2')
   def __init__(self, *args, **kwargs):
      super(SignUpForm, self).__init__(*args, **kwargs)

      self.fields['username'].widget.attrs['class'] = 'form-control'
      self.fields['username'].widget.attrs['placeholder'] = 'Username'
      self.fields['username'].label = ''
      

      self.fields['password1'].widget.attrs['class'] = 'form-control'
      self.fields['password1'].widget.attrs['placeholder'] = 'Password'
      self.fields['password1'].label = ''
      self.fields['password1'].help_text = None

      self.fields['password2'].widget.attrs['class'] = 'form-control'
      self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
      self.fields['password2'].label = ''
      self.fields['password2'].help_text = None
      
      # Remove default help text
      for field_name in self.fields:
         self.fields[field_name].help_text = None
         
   def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role') 
        
        if commit:
            user.save()  # Now save the user first
        
            # Ensure no existing profile is interfering
            UserProfile.objects.filter(user=user).delete()
            
            # Create a UserProfile with the correct role
            profile = UserProfile.objects.create(user=user, role=role)


        return user