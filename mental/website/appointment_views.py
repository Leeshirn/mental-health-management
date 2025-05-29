import json
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import MentalHealthProfessionalForm, PatientProfileForm, AvailabilityForm
from .models import UserProfile, MentalHealthProfessional, PatientProfile, Appointment, Availability,PatientProfessionalRelationship
from django.db import models
from django.db.models import Max, Count
from datetime import timedelta, datetime, date # Import date
from django.utils import timezone
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_datetime, parse_time # Ensure parse_time is imported if used elsewhere

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
    user = request.user
    print(f"DEBUG: User: {user.username}, Role: {user.userprofile.role}")

    if hasattr(user, 'mental_health_pro'):
        print("DEBUG: User HAS 'mental_health_pro' attribute.")
        professional = user.mental_health_pro
        print(f"DEBUG: Professional object found: {professional.user.username}")
    else:
        print("DEBUG: User DOES NOT HAVE 'mental_health_pro' attribute. Falling into patient logic.")
        # This block is for patients viewing a professional
        relationship = PatientProfessionalRelationship.objects.filter(
            patient=user
        ).select_related('professional').first()

        if relationship:
            print(f"DEBUG: Relationship found for patient {user.username} with {relationship.professional.username}")
            if hasattr(relationship.professional, 'mental_health_pro'):
                professional = relationship.professional.mental_health_pro
                print(f"DEBUG: Professional found via relationship: {professional.user.username}")
            else:
                print("DEBUG: Relationship professional does not have mental_health_pro attribute.")
                messages.warning(request, "Error finding professional details via relationship.")
                return redirect('home')
        else:
            print(f"DEBUG: No patient-professional relationship found for {user.username}.")
            messages.warning(request, "You're not currently connected to any professional.")
            return redirect('home')

    context = {
        'professional': professional,
        'approaches': professional.get_approaches_list(),
    }
    return render(request, 'profiles/professional_profile_preview.html', context)

@login_required
def view_professional_profile(request, professional_id):
    professional = get_object_or_404(MentalHealthProfessional, user_id=professional_id)

    context = {
        'professional': professional,
        'approaches': professional.get_approaches_list()
    }
    return render(request, 'profiles/professional_profile_preview.html', context)


# In your views.py (or wherever calendar_view is located)

@login_required
def calendar_view(request):
    user_profile = request.user.userprofile
    connected_professionals = []

    if user_profile.role == 'patient':
        # Corrected query using the 'patients' related_name
        # This filters User objects where the user is the 'professional' in
        # a PatientProfessionalRelationship where the 'patient' is the request.user
        # and the status is 'accepted'.
        connected_professionals = User.objects.filter(
            patients__patient=request.user, # Use 'patients' as the reverse accessor for the professional
            patients__status='accepted'
        ).distinct() # Use .distinct() to avoid duplicate User objects if a patient has multiple relationships with the same professional (though unique_together prevents this, it's good practice for reverse lookups)

        print(f"DEBUG (calendar_view): connected_professionals count: {connected_professionals.count()}")
        for prof in connected_professionals:
            print(f"DEBUG (calendar_view): Connected professional: {prof.username} (ID: {prof.id})")

    elif user_profile.role == 'professional':
        # Professionals don't "connect" to other professionals in this context,
        # so this list would likely be empty or contain themselves if needed for display.
        # For a professional's calendar, you typically show their own availabilities/appointments.
        # This part of the code might not need 'connected_professionals'
        # if the calendar directly uses their own ID.
        pass # Or set connected_professionals = [request.user] if you want them to see their own name in the dropdown.

    context = {
        'user_profile': user_profile,
        'connected_professionals': connected_professionals,
    }
    return render(request, 'professionals/calendar.html', context)
@csrf_exempt
@login_required
def create_from_calendar(request):
    if request.method == 'POST':
        try:
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
                professional = User.objects.get(id=professional_id, userprofile__role='professional')
            except User.DoesNotExist:
                return JsonResponse({'message': 'Selected professional not found.'}, status=400)

            # Check if patient is connected to this professional
            is_connected = PatientProfessionalRelationship.objects.filter(
                patient=request.user,
                professional=professional,
                status='accepted'
            ).exists()
            
            if not is_connected:
                return JsonResponse({'message': 'You are not connected to this professional.'}, status=403)

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
                status__in=['pending', 'approved'] # Corrected 'accepted' to 'approved' if that's your status name
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

        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
        
@login_required
def calendar_data(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    professional_id = request.GET.get('professional_id')
    events = []

    # PATIENT ROLE - Only show connected professionals
    if user_profile.role == 'patient':
        relationships = PatientProfessionalRelationship.objects.filter(
            patient=user,
            status='accepted'
        ).select_related('professional')

        if not relationships.exists():
            return JsonResponse([], safe=False)  # No professionals? Return empty.

        # Determine which professional's data to fetch
        if professional_id == 'all':
            professional_users = [rel.professional for rel in relationships]
            appointments = Appointment.objects.filter(professional__in=professional_users, patient=user)
            availabilities = Availability.objects.filter(professional__in=professional_users)
        elif professional_id: # A specific professional is selected
            try:
                selected_professional = User.objects.get(id=professional_id, userprofile__role='professional')
                # Verify the patient is connected to this selected professional
                if not relationships.filter(professional=selected_professional).exists():
                    return HttpResponseForbidden("Not connected to this professional.")
                appointments = Appointment.objects.filter(professional=selected_professional, patient=user)
                availabilities = Availability.objects.filter(professional=selected_professional)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Selected professional not found.'}, status=404)
        else: # Default if no professional_id (or initial load)
            professional_users = [rel.professional for rel in relationships]
            appointments = Appointment.objects.filter(professional__in=professional_users, patient=user)
            availabilities = Availability.objects.filter(professional__in=professional_users)


    # PROFESSIONAL ROLE
    elif user_profile.role == 'professional':
        professional = user  # always themselves
        appointments = Appointment.objects.filter(professional=professional)
        availabilities = Availability.objects.filter(professional=professional)

    else:
        # Not a valid role/combination
        appointments = []
        availabilities = []

    # ➕ Add availability blocks to calendar
    weekdays = {
        'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
        'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 0
    }

    # For availability, FullCalendar's 'daysOfWeek' expects an array of numbers (0-6)
    # and 'startTime'/'endTime' are just times.
    for slot in availabilities:
        day_index = weekdays.get(slot.day_of_week, None)
        if day_index is None:
            continue

        events.append({
            'id': f"avail-{slot.id}", # Ensure unique ID for availabilities too
            'title': 'Available',
            'daysOfWeek': [day_index],
            'startTime': str(slot.start_time),
            'endTime': str(slot.end_time),
            'display': 'background', # Makes it a background event
            'color': '#d4f5d4',
            'extendedProps': { # <--- ADDED: Extended properties for availability
                'type': 'availability',
                'day_of_week': slot.day_of_week,
                'availability_id': slot.id # Pass availability ID if you ever want to delete it
            }
        })

    # ➕ Add appointments
    for appt in appointments:
        event_color = {
            'pending': '#f0ad4e',
            'approved': '#5cb85c',
            'rejected': '#d9534f',
            'completed': '#5bc0de',
            'cancelled': '#777'
        }.get(appt.status, '#3a87ad')

        # Calculate end time for appointment (assuming 1 hour)
        # Convert appt.time (time object) to a datetime object for timedelta arithmetic
        start_datetime = datetime.combine(appt.date, appt.time)
        end_datetime = start_datetime + timedelta(minutes=60) # Assuming 60 minute appointments

        events.append({
            'id': appt.id,
            'title': (
                appt.patient.username
                if user_profile.role == 'professional'
                else appt.professional.username
            ),
            'start': f"{appt.date.isoformat()}T{appt.time.isoformat()}", # Use isoformat for date and time
            'end': f"{end_datetime.date().isoformat()}T{end_datetime.time().isoformat()}", # Use isoformat for date and time
            'color': event_color,
            'extendedProps': { # <--- ADDED: Extended properties for appointments
                'status': appt.status,
                'notes': appt.notes,
                'reschedule_status': appt.reschedule_status,
                'reschedule_request_date': appt.reschedule_request_date.isoformat() if appt.reschedule_request_date else None,
                'reschedule_request_time': appt.reschedule_request_time.isoformat() if appt.reschedule_request_time else None,
                'reschedule_reason': appt.reschedule_reason,
                'type': 'appointment' # <--- CRITICAL: Defines the event type
            },
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
        # Determine if it's a patient request or a professional action
        is_request = data.get('is_request', 'false') == 'true'
        reschedule_action = data.get('reschedule_action') # 'approve' or 'reject' for professional

        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Check permissions
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.role == 'patient' and appointment.patient != request.user:
                return JsonResponse({"error": "You can only modify your own appointments."}, status=403)
            if user_profile.role == 'professional' and appointment.professional != request.user:
                return JsonResponse({"error": "You can only modify appointments with you."}, status=403)

            # Handle professional approving/rejecting a reschedule request
            if user_profile.role == 'professional' and reschedule_action:
                if appointment.reschedule_status != 'pending':
                    return JsonResponse({"error": "No pending reschedule request for this appointment."}, status=400)

                if reschedule_action == 'approve':
                    # Apply the requested new date/time to the actual appointment
                    if appointment.reschedule_request_date and appointment.reschedule_request_time:
                        appointment.date = appointment.reschedule_request_date
                        appointment.time = appointment.reschedule_request_time
                        appointment.reschedule_status = 'approved'
                        appointment.save()
                        return JsonResponse({"message": "Reschedule request approved. Appointment updated."})
                    else:
                        return JsonResponse({"error": "Reschedule request details are incomplete."}, status=400)
                elif reschedule_action == 'reject':
                    appointment.reschedule_status = 'rejected'
                    appointment.reschedule_request_date = None
                    appointment.reschedule_request_time = None
                    appointment.reschedule_reason = None
                    appointment.save()
                    return JsonResponse({"message": "Reschedule request rejected."})
                else:
                    return JsonResponse({"error": "Invalid reschedule action."}, status=400)

            # Parse new datetime for new reschedule request or direct professional reschedule
            try:
                new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return JsonResponse({"error": "Invalid date/time format."}, status=400)

            # If it's a patient requesting a reschedule
            if is_request and user_profile.role == 'patient':
                # Check for existing pending reschedule request
                if appointment.reschedule_status == 'pending':
                    return JsonResponse({"error": "There is already a pending reschedule request for this appointment."}, status=400)
                
                appointment.reschedule_request_date = new_datetime.date()
                appointment.reschedule_request_time = new_datetime.time()
                appointment.reschedule_reason = reason
                appointment.reschedule_status = 'pending'
                appointment.save()
                return JsonResponse({"message": "Reschedule request submitted. Waiting for professional approval."})
            
            # If it's a professional directly rescheduling (or patient re-requesting after rejection/approval)
            elif user_profile.role == 'professional' or (user_profile.role == 'patient' and appointment.reschedule_status != 'pending'):
                # Professional directly reschedules or patient reschedules an old appointment
                appointment.date = new_datetime.date()
                appointment.time = new_datetime.time()
                # Clear any existing reschedule request data if direct reschedule
                appointment.reschedule_status = None
                appointment.reschedule_request_date = None
                appointment.reschedule_request_time = None
                appointment.reschedule_reason = None

                if reason:
                    # Append or set notes based on existing notes
                    if appointment.notes:
                        appointment.notes = f"{appointment.notes}\nRescheduled: {reason}"
                    else:
                        appointment.notes = f"Rescheduled: {reason}"
                appointment.save()
                return JsonResponse({"message": "Appointment rescheduled successfully."})
            else:
                return JsonResponse({"error": "Invalid reschedule scenario."}, status=400)

        except Appointment.DoesNotExist:
            return JsonResponse({"error": "Appointment not found."}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)


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
            
            # Parse times (handle both HH:MM:SS and HH:MM formats)
            try:
                start_time = parse_time(start_time_str)
                end_time = parse_time(end_time_str)
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
            
            return JsonResponse({'message': 'Availability saved successfully!'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def parse_time(time_str):
    """Helper function to parse time strings in various formats"""
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            raise ValueError("Time must be in HH:MM or HH:MM:SS format")