# admin.py
from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'license_number', 'is_verified')
    list_filter = ('role', 'is_verified')
    search_fields = ('user__username', 'license_number')
    actions = ['verify_professionals']

    def verify_professionals(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, "Selected professionals have been verified.")
    verify_professionals.short_description = "Verify selected professionals"

admin.site.register(UserProfile, UserProfileAdmin)