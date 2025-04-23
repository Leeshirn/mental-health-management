import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages 
from .forms import MentalHealthProfessionalForm, PatientProfileForm, AvailabilityForm
from .models import UserProfile, MentalHealthProfessional, PatientProfile, Appointment, Availability
from django.db import models
from django.db.models import Max, Count
from datetime import timedelta, datetime
from django.utils import timezone

@login_required
def profile_summary_view(request):
    """Default profile view showing summary"""
    profile = get_object_or_404(PatientProfile, user=request.user)
    return render(request, 'profiles/patient_profile_summary.html', {'profile': profile})

@login_required
def edit_profile_view(request):
    """Edit profile view"""
    profile = get_object_or_404(PatientProfile, user=request.user)
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_summary_view')  # Return to summary after save
    else:
        form = PatientProfileForm(instance=profile)
    
    return render(request, 'profiles/patient_edit_profile.html', {'form': form})

@login_required
def professional_profile(request):
    try:
        professional = MentalHealthProfessional.objects.get(user=request.user)
    except MentalHealthProfessional.DoesNotExist:
        professional = MentalHealthProfessional(user=request.user)
    
    if request.method == 'POST':
        form = MentalHealthProfessionalForm(request.POST, request.FILES, instance=professional)
        if form.is_valid():
            # Save the form data regardless of completion
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            form.save_m2m()  # For many-to-many fields
            
            # Update completion status (but don't block saving)
            completed_fields = sum(
                1 for field in MentalHealthProfessionalForm.required_fields 
                if getattr(profile, field) not in [None, '', 0]
            )
            profile.profile_complete = (completed_fields == len(MentalHealthProfessionalForm.required_fields))
            profile.save()
            
            messages.success(request, "Changes saved successfully!")
            return redirect('profile_preview')  # Stay on same page
            
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

@login_required
def calendar_view(request):
    # Check if the user is a professional or patient
    user_profile = UserProfile.objects.get(user=request.user)

    if user_profile.role == 'professional':
        # If the user is a professional, show all appointments involving the professional
        appointments = Appointment.objects.filter(professional=request.user)
    elif user_profile.role == 'patient':
        # If the user is a patient, show only their appointments
        appointments = Appointment.objects.filter(patient=request.user)
    else:
        appointments = []

    return render(request, 'professionals/calendar.html', {'appointments': appointments,'user_profile': user_profile})

@login_required
def calendar_data(request):
    if request.user.is_staff:
        appointments = Appointment.objects.filter(professional=request.user, status='approved')
    else:
        appointments = Appointment.objects.filter(patient=request.user, status='approved')

    data = []
    for appt in appointments:
        data.append({
            'title': f"{appt.patient.username} with {appt.professional.username}",
            'start': f"{appt.date}T{appt.time}",
            'end': f"{appt.date}T{appt.time}",
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
def create_from_calendar(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        date_str = data.get('date')
        time_str = data.get('time')

        # Automatically assign the first available professional (can be improved later)
        professional = User.objects.filter(is_staff=True).first()
        if not professional:
            return JsonResponse({'message': 'No professional available.'}, status=400)

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            return JsonResponse({'message': 'Invalid date/time format.'}, status=400)

        Appointment.objects.create(
            patient=request.user,
            professional=professional,
            date=appt_date,
            time=appt_time,
            status='pending'
        )
        return JsonResponse({'message': 'Appointment requested successfully!'})
