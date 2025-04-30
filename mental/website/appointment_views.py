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
            professional = form.save(commit=False)
            
            # Ensure the user is set before calling form.save()
            if not professional.user_id:
                professional.user = request.user

            form.save()  # This will save both the user and the professional profile
            
            messages.success(request, "Changes saved successfully!")
            return redirect('profile_preview')
        else:
            print("Form errors:", form.errors)  # Debug output
    else:
        form = MentalHealthProfessionalForm(instance=professional)

    return render(request, 'profiles/professional_profile.html', {'form': form})

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
    user_profile = UserProfile.objects.get(user=request.user)

    if user_profile.role == 'professional':
        appointments = Appointment.objects.filter(professional=request.user)
    elif user_profile.role == 'patient':
        appointments = Appointment.objects.filter(patient=request.user)
    else:
        appointments = []

    # Fetch all professionals for patient selection
    professionals = User.objects.filter(userprofile__role='professional', userprofile__is_verified=True)

    return render(request, 'professionals/calendar.html', {
        'appointments': appointments,
        'user_profile': user_profile,
        'professionals': professionals
    })

@csrf_exempt
@login_required
def create_from_calendar(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        date_str = data.get('date')
        time_str = data.get('time')
        professional_id = data.get('professional_id')

        print(f"Received date: {date_str}, time: {time_str}")
        import re
        time_str = re.split(r'[+-]', time_str)[0]  # strips timezone safely

        
        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError as e:
            return JsonResponse({'message': 'Invalid date/time format. Error: {str(e)}'}, status=400)

        # Validate selected professional
        try:
            professional = User.objects.get(id=professional_id, userprofile__role='professional',
            userprofile__is_verified=True)
        except User.DoesNotExist:
            return JsonResponse({'message': 'Selected professional not found.'}, status=400)

        # Check if time falls within the professional's availability
        day_of_week = appt_date.strftime('%A')
        available_slots = Availability.objects.filter(
            professional=professional,
            day_of_week=day_of_week,
            start_time__lte=appt_time,
            end_time__gt=appt_time
        )

        if not available_slots.exists():
            return JsonResponse({'message': 'Selected time is not within the professional’s availability.'}, status=400)

        # Create the appointment
        Appointment.objects.create(
            patient=request.user,
            professional=professional,
            date=appt_date,
            time=appt_time,
            status='pending'
        )
        return JsonResponse({'message': 'Appointment requested successfully!'})

@login_required
def calendar_data(request):
    if request.user.is_staff:
        appointments = Appointment.objects.filter(professional=request.user, status='approved')
    else:
        appointments = Appointment.objects.filter(patient=request.user, status='approved')

    availability = Availability.objects.filter(professional=request.user)
    availability_data = []
    for slot in availability:
        availability_data.append({
            'title': 'Available',
            'start': f"{slot.day_of_week}T{slot.start_time}",
            'end': f"{slot.day_of_week}T{slot.end_time}",
            'color': 'green',  # Optional: color for availability
        })
    
    data = []
    for appt in appointments:
        data.append({
            'title': f"{appt.patient.username} with {appt.professional.username}",
            'start': f"{appt.date}T{appt.time}",
            'end': f"{appt.date}T{appt.time}",
        })
    return JsonResponse(data, safe=False)

# views.py


from .forms import AvailabilityForm 

@login_required
def manage_availability(request):
    if request.user.userprofile.role != 'professional':
        return redirect('home')  # Redirect to home if user is not a professional

    availability_slots = Availability.objects.filter(professional=request.user)

    if request.method == "POST":
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.professional = request.user
            availability.save()
            return redirect('manage_availability')
    else:
        form = AvailabilityForm()

    return render(request, 'professionals/manage_availability.html', {
        'form': form,
        'availability_slots': availability_slots
    })


@csrf_exempt
@login_required
def save_availability(request):
    if request.method == "POST" and request.user.profile.role == 'professional':
        data = json.loads(request.body)
        start = parse_datetime(data.get("start"))
        end = parse_datetime(data.get("end"))

        Availability.objects.create(
            professional=request.user,
            date=start.date(),
            start_time=start.time(),
            end_time=end.time()
        )
        return JsonResponse({"message": "Availability saved successfully."})
    return JsonResponse({"error": "Unauthorized or invalid request."}, status=400)
