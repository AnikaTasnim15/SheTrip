from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'age', 'travel_style']
    search_fields = ['user__username', 'city', 'country']

admin.site.register(UserProfile, UserProfileAdmin)