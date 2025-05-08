import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages 
from .forms import MentalHealthProfessionalForm, PatientProfileForm, AvailabilityForm,PatientConsentForm
from .models import UserProfile, MentalHealthProfessional, PatientProfile, Appointment, Availability,UserProfile, MoodEntry,JournalEntry, JournalSettings, JournalPrompt, PatientProfessionalRelationship
from django.db import models
from django.db.models import Max, Count
from datetime import timedelta, datetime
from django.utils import timezone
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_datetime
from django.core.exceptions import PermissionDenied

@login_required
def professional_patient_dashboard(request):
    profile = request.user.userprofile
    if profile.role != 'professional' or not profile.is_verified:
        return redirect('home')

    patients = User.objects.filter(
        care_team__professional=request.user
    ).select_related('userprofile')

    return render(request, 'professionals/patient_dashboard.html', {'patients': patients
})
    
@login_required
def explore_professionals(request):
    professionals = MentalHealthProfessional.objects.filter(profile_complete=True)
    
    context = {
        'professionals': professionals,
    }
    return render(request, 'profiles/explore_professionals.html', context)



@login_required
def my_professional_view(request):
    if request.user.userprofile.role != 'patient':
        raise PermissionDenied

    relationship = PatientProfessionalRelationship.objects.filter(
        patient=request.user
    ).select_related('professional').first()

    professional_profile = None
    if relationship:
        professional_profile = MentalHealthProfessional.objects.filter(
            user=relationship.professional
        ).first()

    return render(request, 'profiles/professional_profile_preview.html', {
        'professional': professional_profile
    })

    

@login_required
def view_patient_mood(request, patient_id):
    patient = get_object_or_404(User, pk=patient_id)
    relationship = get_object_or_404(
        PatientProfessionalRelationship,
        professional=request.user,
        patient=patient
    )

    if not relationship.access_mood:
        raise PermissionDenied

    mood_entries = MoodEntry.objects.filter(user=patient).order_by('-date_logged')
    
    # Same mood_data preparation as in patient's mood_history
    return render(request, 'mood_tracker/mood_history.html', {
        'patient': patient,
        'mood_entries': mood_entries
    })

@login_required
def view_patient_journal(request, patient_id):
    patient = get_object_or_404(User, pk=patient_id)
    relationship = get_object_or_404(
        PatientProfessionalRelationship,
        professional=request.user,
        patient=patient
    )

    if not relationship.access_journal:
        raise PermissionDenied

    entries = JournalEntry.objects.filter(
        user=patient,
        visibility__in=['care_team', 'public']
    )

    if relationship.journal_access_level == 'summary':
        # Show only sentiment analysis
        pass
    elif relationship.journal_access_level == 'titles':
        entries = entries.only('title', 'created_at')
    
    return render(request, 'journal/dashboard.html', {
        'patient': patient,
        'entries': entries,
        'access_level': relationship.journal_access_level
    })
    
@login_required
def privacy_settings(request):
    if not request.user.userprofile.role == 'patient':
        return redirect('home')

    relationships = PatientProfessionalRelationship.objects.filter(
        patient=request.user
    ).select_related('professional')

    return render(request, 'patient/privacy_settings.html', {
        'relationships': relationships
    })

@login_required
def update_consent(request, relationship_id):
    relationship = get_object_or_404(
        PatientProfessionalRelationship,
        pk=relationship_id,
        patient=request.user
    )

    if request.method == 'POST':
        form = PatientConsentForm(request.POST, instance=relationship)
        if form.is_valid():
            form.save()
            return redirect('privacy_settings')
    else:
        form = PatientConsentForm(instance=relationship)

    return render(request, 'patient/update_consent.html', {
        'form': form,
        'professional': relationship.professional
    })