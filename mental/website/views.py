import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages 
from .forms import SignUpForm, MoodEntryForm, JournalEntryForm, JournalSettingsForm, MentalHealthProfessionalForm, PatientProfileForm
from .models import UserProfile, MoodEntry,JournalEntry, JournalSettings, JournalPrompt, MentalHealthProfessional, PatientProfile
from django.db import models
from django.db.models import Max, Count
from datetime import timedelta, datetime
from django.utils import timezone


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

@login_required
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
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date_logged')
    
    # Prepare data for Chart.js
    mood_data = {
        "dates": [entry.date_logged.strftime('%Y-%m-%d') for entry in mood_entries],
        "scores": [entry.score for entry in mood_entries],
    }

    return render(request, 'mood_tracker/mood_history.html', {
        'mood_entries': mood_entries,  # Use 'mood_entries' to match the template
        'mood_data': json.dumps(mood_data)  # Send JSON data to the template
    })
    
@login_required
def update_mood(request, entry_id):
    entry = get_object_or_404(MoodEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        form = MoodEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('mood_history')
    else:
        form = MoodEntryForm(instance=entry)
    return render(request, 'mood_tracker/update_mood.html', {'form': form, 'entry': entry})

@login_required
def delete_mood_entry(request, entry_id):
    entry = get_object_or_404(MoodEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        entry.delete()
        return redirect('mood_history')
    return render(request, 'mood_tracker/confirm_delete.html', {'entry': entry})

@login_required
def mood_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    period = request.GET.get('period')  # New line

    today = timezone.now().date()
    error_message = None

    if period == 'weekly':
        end_date = today
        start_date = end_date - timedelta(days=6)  # Go 6 days back, today is included
    elif period == 'monthly':
        start_date = today.replace(day=1)
        next_month = start_date + timedelta(days=32)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    elif start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        if start_date > today:
            error_message = "Start date cannot be in the future."
        elif start_date > end_date:
            error_message = "Start date cannot be after the end date."
    else:
        start_date = today
        end_date = today

    if error_message:
        return render(request, 'mood_tracker/mood_report.html', {
            'error_message': error_message,
            'start_date': today,
            'end_date': today,
            'mood_counts': [],
            'total_entries': 0,
            'mood_data': json.dumps({"dates": [], "scores": []}),
        })

    end_date_with_time = datetime.combine(end_date, datetime.max.time())
    start_date_with_time = datetime.combine(start_date, datetime.min.time())

    entries = MoodEntry.objects.filter(user=request.user, date_logged__range=[start_date_with_time, end_date_with_time])
    mood_counts = entries.values('mood').annotate(count=Count('mood')).order_by('mood')
    total_entries = entries.count()

    mood_data = {
        "dates": [entry.date_logged.strftime('%Y-%m-%d %H:%M:%S') for entry in entries],
        "scores": [entry.score for entry in entries],
    }

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'mood_counts': mood_counts,
        'total_entries': total_entries,
        'mood_data': json.dumps(mood_data),
    }
    return render(request, 'mood_tracker/mood_report.html', context)


@login_required
def journal_dashboard(request):
    """ Display all journal entries and settings for the logged-in user """
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')

    
    return render(request, 'journal/dashboard.html', {'entries': entries})

@login_required
def create_journal_entry(request):
    """ Allow the user to write a new journal entry """
    prompt_text = JournalPrompt.get_random_prompt()
    
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.user = request.user
            journal_entry.save()
            return redirect('journal_dashboard')
        else:
            print(form.errors)
    else:
        form = JournalEntryForm()
    
    return render(request, 'journal/new_entry.html', {'form': form, 'prompt': prompt_text})

@login_required
def edit_journal_entry(request, entry_id):
    """ Allow users to edit their journal entry """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)

    if request.method == 'POST':
        form = JournalEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('journal_dashboard')
    else:
        form = JournalEntryForm(instance=entry)

    return render(request, 'journal/edit_entry.html', {'form': form})

@login_required
def delete_journal_entry(request, entry_id):
    """ Allow users to delete their journal entry """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)

    if request.method == 'POST':
        entry.delete()
        return redirect('journal_dashboard')

    return render(request, 'journal/confirm_delete.html', {'entry': entry})

@login_required
def update_journal_settings(request):
    """ Allow users to update their journal prompt frequency """
    settings, _ = JournalSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = JournalSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('journal_dashboard')
    else:
        form = JournalSettingsForm(instance=settings)

    return render(request, 'journal/settings.html', {'form': form})

@login_required
def profile_view(request):
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=profile)  
        if form.is_valid():
            form.save()
            return redirect('profile_view')
    else:
        form = PatientProfileForm(instance=profile)
    return render(request, 'profiles/patient_profile.html', {'form': form, 'profile': profile})

@login_required
def edit_profile_view(request):
    profile, _ = PatientProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_summary')  # Redirect to summary after saving
    else:
        form = PatientProfileForm(instance=profile)

    return render(request, 'profiles/patient_edit_profile.html', {'form': form})

@login_required
def profile_summary_view(request):
    profile = PatientProfile.objects.get(user=request.user)
    return render(request, 'profiles/patient_profile_summary.html', {'profile': profile})


@login_required
def professional_profile(request):
    try:
        # Try to get existing profile or create with safe defaults
        professional, created = MentalHealthProfessional.objects.get_or_create(
            user=request.user,
            defaults={
                'session_fee': 0,
            
                
            }
        )
        
        if created:
            messages.info(request, "Welcome! Please complete your professional profile.")

    except Exception as e:
        messages.error(request, f"Error accessing profile: {str(e)}")
        return redirect('home')

    if request.method == 'POST':
        form = MentalHealthProfessionalForm(request.POST, request.FILES, instance=professional)
        if form.is_valid():
            # Ensure user field isn't overwritten
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            form.save_m2m()  # For many-to-many fields
            
            # Update completion status (customize your logic)
            required_fields_complete = all(
                getattr(profile, field) not in [None, '', 0] 
                for field in MentalHealthProfessionalForm.required_fields
            )
            profile.profile_complete = required_fields_complete
            profile.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect('professional_profile')
    else:
        form = MentalHealthProfessionalForm(instance=professional)

    context = {
        'form': form,
        'professional': professional,
        'profile_complete': professional.profile_complete,
    }
    return render(request, 'profiles/professional_profile.html', context)

@login_required
def profile_preview(request):
    try:
        professional = request.user.mental_health_pro
    except MentalHealthProfessional.DoesNotExist:
        messages.error(request, "This account is not registered as a mental health professional.")
        return redirect('home')
    
    context = {
        'professional': professional,
        'approaches': professional.get_approaches_list(),
    }
    return render(request, 'profiles/professional_profile_preview.html', context)