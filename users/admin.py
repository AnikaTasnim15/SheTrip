from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, UserConnection, Notification, SupportTicket

admin.site.unregister(User)

class CustomUserAdmin(BaseUserAdmin):
    actions = ['delete_selected']

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' not in actions and request.user.is_superuser:
            from django.contrib.admin.actions import delete_selected
            actions['delete_selected'] = (delete_selected, 'delete_selected', delete_selected.short_description)
        return actions

admin.site.register(User, CustomUserAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'age', 'travel_style', 'verification_status', 'nid_thumbnail']
    search_fields = ['user__username', 'city', 'country']
    list_filter = ['verification_status', 'city', 'country']
    actions = ['delete_profile_and_user', 'approve_verification', 'reject_verification']
    readonly_fields = ['nid_front_preview', 'nid_back_preview', 'submitted_at', 'verified_at']

    def nid_thumbnail(self, obj):
        if obj.nid_front:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" /></a>',
                obj.nid_front.url,
                obj.nid_front.url
            )
        return "No image"
    nid_thumbnail.short_description = 'NID Preview'

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
        count = queryset.count()
        for profile in queryset:
            user = profile.user
            user.delete()
        self.message_user(request, f"{count} user(s) and their profile(s) deleted successfully.")
    delete_profile_and_user.short_description = "Delete selected profiles and users"

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    fieldsets = (
        ('User Information', {'fields': ('user',)}),
        ('Personal Details', {'fields': ('age', 'phone', 'city', 'country', 'occupation')}),
        ('Travel Preferences', {'fields': ('languages', 'travel_style', 'accommodation', 'interests', 'dream_destinations', 'bio')}),
        ('Verification Documents', {'fields': ('verification_status', 'nid_front_preview', 'nid_back_preview', 'submitted_at', 'verified_at', 'admin_notes')}),
        ('Profile Picture', {'fields': ('profile_picture',)}),
    )

admin.site.register(UserProfile, UserProfileAdmin)

@admin.register(UserConnection)
class UserConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['created_at', 'updated_at']

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'connected': '#10b981',
            'blocked': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['mark_connected', 'mark_blocked']

    def mark_connected(self, request, queryset):
        count = queryset.update(status='connected')
        self.message_user(request, f'{count} connection(s) marked as connected.')
    mark_connected.short_description = 'Mark as connected'

    def mark_blocked(self, request, queryset):
        count = queryset.update(status='blocked')
        self.message_user(request, f'{count} user(s) blocked.')
    mark_blocked.short_description = 'Block users'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'message', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'message']
    readonly_fields = ['created_at']

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'user', 'subject', 'category', 'priority', 'status', 'created_at']
    list_filter = ['status', 'category', 'priority', 'created_at']
    search_fields = ['subject', 'message', 'user__username', 'email']
    readonly_fields = ['ticket_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Ticket Info', {'fields': ('ticket_id', 'user', 'status', 'created_at', 'updated_at')}),
        ('Contact Details', {'fields': ('name', 'email', 'phone')}),
        ('Issue Details', {'fields': ('subject', 'category', 'priority', 'message')}),
        ('Admin Response', {'fields': ('admin_response',)}),
    )
