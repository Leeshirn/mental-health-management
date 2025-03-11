import json
from django.http import JsonResponse
from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages 
from .forms import SignUpForm, MoodEntryForm
from .models import UserProfile, MoodEntry
from django.db import models



def home(request):
    return render(request, 'home.html', {})
 
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': 'patient', 'is_verified': True})

            # Check if professional needs verification
            if profile.role == 'professional' and not profile.is_verified:
                messages.warning(request, 'Your account is pending verification. Please wait for admin approval.')
                return redirect('login')

            login(request, user)
            messages.success(request, 'You have been logged in.')

            # Redirect based on role
            if profile.role == 'professional':
                return redirect('professional_dashboard')
            else:
                return redirect('patient_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html', {})

  
def logout_user(request):
  logout(request)
  messages.success(request, 'You have been logged out ')
  return redirect('home')

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
          form.save()
          username = form.cleaned_data['username']
          password = form.cleaned_data['password1']
          user = authenticate(username=username, password=password)
          role = form.cleaned_data['role']

          if role == 'patient':
            messages.success(request, 'You have successfully registered. Please log in.')
            return redirect('login')
          else:
            messages.success(request, 'Your account is pending verification. You will be notified once verified.')
            return redirect('pending_verification')  # Redirect to a "pending verification" page
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

@login_required
def professional_dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    if profile.role != 'professional':
        messages.error(request, 'Unauthorized access.')
        return redirect('home')

    if not profile.is_verified:
        messages.warning(request, 'Your account is pending verification.')
        return redirect('home')

    return render(request, 'professional_dashboard.html', {})

def pending_verification(request):
    return render(request, 'pending_verification.html', {})

@login_required
def patient_dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    if profile.role != 'patient':
        messages.error(request, 'Unauthorized access.')
        return redirect('home')

    return render(request, 'patient_dashboard.html')

def log_mood(request):
    if request.method == 'POST':
        form = MoodEntryForm(request.POST)
        if form.is_valid():
            mood_entry = form.save(commit=False)
            mood_entry.user = request.user
            mood_entry.save()  # Sentiment is auto-calculated in the model
            return redirect('mood_history')
    else:
        form = MoodEntryForm()
    
    return render(request, 'mood_tracker/log_mood.html', {'form': form})

@login_required
def mood_history(request):
    moods = MoodEntry.objects.filter(user=request.user).order_by('-date')
    
    # Prepare data for Chart.js
    mood_data = {
        "dates": [entry.date.strftime('%Y-%m-%d') for entry in moods],
        "mood_scores": [entry.mood_score for entry in moods],
        "sentiment_scores": [entry.sentiment_score for entry in moods]
    }

    return render(request, 'mood_tracker/mood_history.html', {
        'moods': moods,
        'mood_data': json.dumps(mood_data)  # Send JSON data to the template
    })