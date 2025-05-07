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
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_datetime

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

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError as e:
            return JsonResponse({'message': f'Invalid date/time format. Error: {str(e)}'}, status=400)

        try:
            professional = User.objects.get(id=professional_id, userprofile__role='professional', userprofile__is_verified=True)
        except User.DoesNotExist:
            return JsonResponse({'message': 'Selected professional not found.'}, status=400)

        # Check availability
        day_of_week = appt_date.strftime('%A')
        available_slots = Availability.objects.filter(
            professional=professional,
            day_of_week=day_of_week,
            start_time__lte=appt_time,
            end_time__gt=appt_time
        )

        if not available_slots.exists():
            return JsonResponse({'message': "Selected time is not within the professional's availability."}, status=400)

        # Check for existing appointment at this time
        existing_appt = Appointment.objects.filter(
            professional=professional,
            date=appt_date,
            time=appt_time,
            status__in=['pending', 'approved']
        ).exists()

        if existing_appt:
            return JsonResponse({'message': 'This time slot is already booked.'}, status=400)

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
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    professional_id = request.GET.get('professional_id')

    events = []

    if user_profile.role == 'patient' and professional_id:
        try:
            professional = User.objects.get(id=professional_id)
        except User.DoesNotExist:
            return JsonResponse([], safe=False)

        appointments = Appointment.objects.filter(professional=professional, patient=user)
        availabilities = Availability.objects.filter(professional=professional)

    elif user_profile.role == 'professional':
        appointments = Appointment.objects.filter(professional=user)
        availabilities = Availability.objects.filter(professional=user)

    else:
        appointments = []
        availabilities = []

    # Add availability blocks
    for slot in availabilities:
        weekdays = {
            'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
            'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 0
        }
        day_index = weekdays.get(slot.day_of_week, None)
        if day_index is None:
            continue

        events.append({
            'title': 'Available',
            'daysOfWeek': [day_index],
            'startTime': str(slot.start_time),
            'endTime': str(slot.end_time),
            'display': 'background',
            'color': '#d4f5d4',
        })

    # Add appointments
    for appt in appointments:
        event_color = {
            'pending': '#f0ad4e',
            'approved': '#5cb85c',
            'rejected': '#d9534f',
            'completed': '#5bc0de',
            'cancelled': '#777'
        }.get(appt.status, '#3a87ad')

        events.append({
            'id': appt.id,
            'title': f"{appt.patient.username if user_profile.role == 'professional' else appt.professional.username}",
            'start': f"{appt.date}T{appt.time}",
            'end': f"{appt.date}T{appt.time}",
            'status': appt.status,
            'color': event_color,
            'notes': appt.notes,
            'editable': user_profile.role == 'professional' and appt.status == 'approved'
        })

    return JsonResponse(events, safe=False)

@csrf_exempt
@login_required
def update_appointment_status(request):
    if request.method == "POST":
        data = json.loads(request.body)
        appointment_id = data.get('appointment_id')
        new_status = data.get('status')

        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Check permissions
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.role == 'patient' and appointment.patient != request.user:
                return JsonResponse({"error": "You can only modify your own appointments."}, status=403)
            if user_profile.role == 'professional' and appointment.professional != request.user:
                return JsonResponse({"error": "You can only modify appointments with you."}, status=403)

            # Update status
            appointment.status = new_status
            appointment.save()
            return JsonResponse({"message": f"Appointment status updated to {new_status}."})
        except Appointment.DoesNotExist:
            return JsonResponse({"error": "Appointment not found."}, status=404)

    return JsonResponse({"error": "Invalid request."}, status=400)

@csrf_exempt
@login_required
def reschedule_appointment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        appointment_id = data.get('appointment_id')
        new_date = data.get('new_date')
        new_time = data.get('new_time')
        reason = data.get('reason', '')
        is_request = data.get('is_request', 'false') == 'true'

        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Check permissions
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.role == 'patient' and appointment.patient != request.user:
                return JsonResponse({"error": "You can only reschedule your own appointments."}, status=403)
            if user_profile.role == 'professional' and appointment.professional != request.user:
                return JsonResponse({"error": "You can only reschedule appointments with you."}, status=403)

            # Parse new datetime
            try:
                new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return JsonResponse({"error": "Invalid date/time format."}, status=400)

            # For patients, create a reschedule request
            if is_request and user_profile.role == 'patient':
                appointment.reschedule_request_date = new_datetime.date()
                appointment.reschedule_request_time = new_datetime.time()
                appointment.reschedule_reason = reason
                appointment.reschedule_status = 'pending'
                appointment.save()
                return JsonResponse({"message": "Reschedule request submitted. Waiting for professional approval."})
            
            # For professionals, reschedule immediately
            appointment.date = new_datetime.date()
            appointment.time = new_datetime.time()
            if reason:
                appointment.notes = f"Rescheduled: {reason}"
            appointment.save()
            return JsonResponse({"message": "Appointment rescheduled successfully."})
        except Appointment.DoesNotExist:
            return JsonResponse({"error": "Appointment not found."}, status=404)

    return JsonResponse({"error": "Invalid request."}, status=400)

@csrf_exempt
@login_required
def save_availability(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            day_of_week = data.get('day_of_week')
            start_time_str = data.get('start_time')
            end_time_str = data.get('end_time')
            
            # Validate required fields
            if not all([day_of_week, start_time_str, end_time_str]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            # Parse times
            try:
                start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
                end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
            except ValueError as e:
                return JsonResponse({'error': f'Invalid time format: {str(e)}'}, status=400)
            
            # Check if end time is after start time
            if end_time <= start_time:
                return JsonResponse({'error': 'End time must be after start time'}, status=400)
            
            # Create availability slot
            Availability.objects.create(
                professional=request.user,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time
            )
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)