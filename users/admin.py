from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile

admin.site.unregister(User)

class CustomUserAdmin(BaseUserAdmin):
    # Enable the delete action
    actions = ['delete_selected']
    
    # Override to ensure delete permission is granted
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    # Make sure delete_selected action is available
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' not in actions and request.user.is_superuser:
            from django.contrib.admin.actions import delete_selected
            actions['delete_selected'] = (delete_selected, 'delete_selected', delete_selected.short_description)
        return actions

# Register User with custom admin
admin.site.register(User, CustomUserAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'age', 'travel_style', 'verification_status', 'nid_thumbnail']
    search_fields = ['user__username', 'city', 'country']
    list_filter = ['verification_status', 'city', 'country']
    actions = ['delete_profile_and_user', 'approve_verification', 'reject_verification']
    
    # Add readonly fields for detail view
    readonly_fields = ['nid_front_preview', 'nid_back_preview', 'submitted_at', 'verified_at']
    
    # Thumbnail in list view
    def nid_thumbnail(self, obj):
        if obj.nid_front:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" /></a>',
                obj.nid_front.url,
                obj.nid_front.url
            )
        return "No image"
    nid_thumbnail.short_description = 'NID Preview'
    
    # Full preview for detail view
    def nid_front_preview(self, obj):
        if obj.nid_front:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.nid_front.url
            )
        return "No image uploaded"
    nid_front_preview.short_description = 'NID Front Side'
    
    def nid_back_preview(self, obj):
        if obj.nid_back:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.nid_back.url
            )
        return "No image uploaded"
    nid_back_preview.short_description = 'NID Back Side'


    def approve_verification(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(verification_status='verified', verified_at=timezone.now())
        self.message_user(request, f"{count} user(s) verified successfully.")
    approve_verification.short_description = "Approve selected verifications"
    
    def reject_verification(self, request, queryset):
        count = queryset.update(verification_status='rejected')
        self.message_user(request, f"{count} verification(s) rejected.")
    reject_verification.short_description = "Reject selected verifications"

    def delete_profile_and_user(self, request, queryset):
        """Delete user profiles along with their associated users"""
        count = queryset.count()
        for profile in queryset:
            user = profile.user
            user.delete()  # This will cascade and delete the profile too
        self.message_user(request, f"{count} user(s) and their profile(s) deleted successfully.")
    
    delete_profile_and_user.short_description = "Delete selected profiles and users"
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']  # Remove default delete to avoid confusion
        return actions
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Details', {
            'fields': ('age', 'phone', 'city', 'country', 'occupation')
        }),
        ('Travel Preferences', {
            'fields': ('languages', 'travel_style', 'accommodation', 'interests', 'dream_destinations', 'bio')
        }),
        ('Verification Documents', {
            'fields': ('verification_status', 'nid_front_preview', 'nid_back_preview', 'submitted_at', 'verified_at', 'admin_notes'),
        }),
        ('Profile Picture', {
            'fields': ('profile_picture',)
        }),
    )

admin.site.register(UserProfile, UserProfileAdmin)