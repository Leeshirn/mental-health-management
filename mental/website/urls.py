from django.urls import path  
from . import views

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
    path('professional_profile/', views.professional_profile, name='professional_profile'),
    path('profile_preview/', views.profile_preview, name='profile_preview'),
    path('profile_view/', views.profile_view, name='profile_view'),
    path('edit_profile_view/', views.edit_profile_view, name='edit_profile_view'),
    path('profile_summary_view/', views.profile_summary_view, name='profile_summary_view'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('calendar-data/', views.calendar_data, name='calendar_data'),
    path('create-from-calendar/', views.create_from_calendar, name='create_from_calendar'),
]
