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
    
    professionals = MentalHealthProfessional.objects.filter(profile_complete=True).select_related('user')

    # Get all relationships for the current patient
    relationships = PatientProfessionalRelationship.objects.filter(
        patient=request.user
    )

    # Build a dictionary for quick lookup: {professional_user_id: status}
    relationship_dict = {rel.professional.id: rel for rel in relationships}

    # Add status info to each professional
    for professional in professionals:
        rel = relationship_dict.get(professional.user.id)
        if rel:
            professional.connection_status = rel.status
            professional.rejection_reason = rel.rejection_reason
        else:
            professional.connection_status = None
            professional.rejection_reason = ''

    context = {
        'professionals': professionals,
    }
    return render(request, 'profiles/explore_professionals.html', context)

@login_required
def request_connection(request, professional_id):
    professional = get_object_or_404(User, id=professional_id)

    if professional == request.user:
        messages.warning(request, "You can't connect with yourself.")
        return redirect('explore_professionals')

    relationship, created = PatientProfessionalRelationship.objects.get_or_create(
        patient=request.user,
        professional=professional,
        defaults={'status': 'pending'}
    )

    if not created:
        if relationship.status == 'pending':
            messages.info(request, "You’ve already sent a request.")
        elif relationship.status == 'accepted':
            messages.info(request, "You’re already connected.")
        else:
            # Reset status to pending and clear rejection reason
            relationship.status = 'pending'
            relationship.rejection_reason = ''
            relationship.save()
            messages.success(request, "Request re-sent.")
    else:
        messages.success(request, "Connection request sent.")

    return redirect('explore_professionals')


@login_required
def respond_to_request(request, relationship_id, action):
    relationship = get_object_or_404(
        PatientProfessionalRelationship, 
        id=relationship_id, 
        professional=request.user
    )

    if request.method == 'POST':
        if action == 'accept':
            relationship.status = 'accepted'
            relationship.rejection_reason = ''
            messages.success(request, "Request accepted.")
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '').strip()
            relationship.status = 'rejected'
            relationship.rejection_reason = reason
            messages.info(request, "Request rejected with reason.")
        else:
            messages.error(request, "Invalid action.")
            return redirect('pending_requests')

        relationship.save()

    return redirect('pending_requests')



@login_required
def pending_requests(request):
    requests = PatientProfessionalRelationship.objects.filter(
        professional=request.user,
        status='pending'
    ).select_related('patient')
    return render(request, 'professionals/pending_requests.html', {'requests': requests})


@login_required
def handle_connection_request(request, request_id):
    relationship = get_object_or_404(PatientProfessionalRelationship, id=request_id)

    if relationship.professional != request.user:
        raise PermissionDenied

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "accept":
            relationship.status = "accepted"
            relationship.rejection_reason = None  # clear if previously set
            messages.success(request, "Connection accepted.")
        elif action == "reject":
            reason = request.POST.get("rejection_reason", "").strip()
            relationship.status = "rejected"
            relationship.rejection_reason = reason
            messages.info(request, "Connection rejected with reason.")
        else:
            messages.error(request, "Invalid action.")
            return redirect('pending_requests')

        relationship.save()

    return redirect('pending_requests')


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
        'professional': professional_profile,
        'relationship': relationship,
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