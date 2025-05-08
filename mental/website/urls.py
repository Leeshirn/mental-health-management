from django.urls import path  
from . import views
from . import appointment_views
from . import relationship_views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("professional_dashboard/", views.professional_dashboard, name='professional_dashboard'),
    path("pending_verification/", views.pending_verification, name='pending_verification'),
    path('patient_dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('log_mood/', views.log_mood, name='log_mood'),
    path('mood_history/', views.mood_history, name='mood_history'),
    path('update_mood/<int:entry_id>/', views.update_mood, name='update_mood'),
    path('delete/<int:entry_id>/', views.delete_mood_entry, name='delete_mood_entry'),
    path('mood-report/', views.mood_report, name='mood_report'), 
    path('journal/', views.journal_dashboard, name='journal_dashboard'),
    path('journal/new/', views.create_journal_entry, name='create_journal_entry'),
    path('journal/edit/<int:entry_id>/', views.edit_journal_entry, name='edit_journal_entry'),
    path('journal/delete/<int:entry_id>/', views.delete_journal_entry, name='delete_journal_entry'),
    path('journal/settings/', views.update_journal_settings, name='update_journal_settings'),
    path('professional_profile/', appointment_views.professional_profile, name='professional_profile'),
    path('profile_preview/', appointment_views.profile_preview, name='profile_preview'),
    path('view_professional_profile/<int:professional_id>/', appointment_views.view_professional_profile, name='view_professional_profile'),
    path('edit_profile_view/', appointment_views.edit_profile_view, name='edit_profile_view'),
    path('profile_summary_view/', appointment_views.profile_summary_view, name='profile_summary_view'),
    path('calendar/', appointment_views.calendar_view, name='calendar_view'),
    path('calendar-data/', appointment_views.calendar_data, name='calendar_data'),
    path('create-from-calendar/', appointment_views.create_from_calendar, name='create_from_calendar'),
    path('update-appointment-status/', appointment_views.update_appointment_status, name='update_appointment_status'),
    path('reschedule_appointment/', appointment_views.reschedule_appointment, name='reschedule_appointment'),
    path('save-availability/', appointment_views.save_availability, name='save_availability'),
    path('professional_patient_dashboard/', relationship_views.professional_patient_dashboard, name='professional_patient_dashboard'),
    path('view_patient_mood/<int:patient_id>/mood/', relationship_views.view_patient_mood, name='view_patient_mood'),
    path('view_patient_journal/<int:patient_id>/journal/', relationship_views.view_patient_journal, name='view_patient_journal'),
    path('privacy-settings/', relationship_views.privacy_settings, name='privacy_settings'),
    path('update_consent/<int:relationship_id>/', relationship_views.update_consent, name='update_consent'),
    path('my-professional/', relationship_views.my_professional_view, name='my_professional'),
    path('explore-professionals/', relationship_views.explore_professionals, name='explore_professionals'),
    path('request-connection/<int:professional_id>/', relationship_views.request_connection, name='request_connection'),
    path('pending-requests/', relationship_views.pending_requests, name='pending_requests'),
    path('respond-request/<int:relationship_id>/<str:action>/', relationship_views.respond_to_request, name='respond_to_request'),
    path('handle_connection_request/<int:request_id>/', relationship_views.handle_connection_request, name='handle_connection_request'),
    path('shared_notes_view/<int:relationship_id>/notes/', relationship_views.shared_notes_view, name='shared_notes_view'),


]
