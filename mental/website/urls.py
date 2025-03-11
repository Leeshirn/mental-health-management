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
    path('mood_history/', views.mood_history, name='mood_history')
]
