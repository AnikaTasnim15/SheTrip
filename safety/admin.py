from django.contrib import admin
from django.utils.html import format_html
from .models import SafetyReport, SafetyGuideline, EmergencyContact, SOSAlert


@admin.register(SafetyReport)
class SafetyReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'reporter', 'report_type', 'severity_badge', 'status', 'created_at', 'resolved']
    list_filter = ['resolved', 'status', 'severity_level', 'report_type', 'created_at']
    search_fields = ['title', 'description', 'reporter__username', 'reporter__email']
    readonly_fields = ['created_at', 'resolved_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'title', 'report_type', 'description', 'location')
        }),
        ('Assessment', {
            'fields': ('severity_level', 'status', 'admin_notes')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def severity_badge(self, obj):
        colors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444',
            'critical': '#7f1d1d'
        }
        color = colors.get(obj.severity_level, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_severity_level_display()
        )

    severity_badge.short_description = 'Severity'

    actions = ['mark_as_resolved', 'mark_as_investigating']

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(resolved=True, status='resolved')
        self.message_user(request, f'{updated} report(s) marked as resolved.')

    mark_as_resolved.short_description = "Mark selected reports as resolved"

    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating')
        self.message_user(request, f'{updated} report(s) marked as under investigation.')

    mark_as_investigating.short_description = "Mark as under investigation"


@admin.register(SafetyGuideline)
class SafetyGuidelineAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'priority']
    search_fields = ['title', 'content', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['priority', 'is_active']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'icon')
        }),
        ('Content', {
            'fields': ('short_description', 'content')
        }),
        ('Settings', {
            'fields': ('priority', 'is_active')
        }),
    )


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['contact_name', 'user', 'relationship', 'phone_number', 'is_primary', 'created_at']
    list_filter = ['relationship', 'is_primary', 'created_at']
    search_fields = ['contact_name', 'user__username', 'phone_number', 'email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'relationship', 'phone_number', 'alternate_phone', 'email')
        }),
        ('Settings', {
            'fields': ('is_primary',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'status_badge', 'location_display', 'timestamp', 'contacts_notified']
    list_filter = ['status', 'alert_type', 'contacts_notified', 'timestamp']
    search_fields = ['user__username', 'description', 'location_address']
    readonly_fields = ['timestamp', 'resolved_at', 'notification_sent_at']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Alert Information', {
            'fields': ('user', 'alert_type', 'description')
        }),
        ('Location', {
            'fields': ('location_latitude', 'location_longitude', 'location_address')
        }),
        ('Status', {
            'fields': ('status', 'resolved_by', 'admin_notes')
        }),
        ('Notifications', {
            'fields': ('contacts_notified', 'notification_sent_at')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'active': '#ef4444',
            'responding': '#f59e0b',
            'resolved': '#10b981',
            'false_alarm': '#6b7280'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def location_display(self, obj):
        if obj.location_latitude and obj.location_longitude:
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank">📍 View on Map</a>',
                obj.location_latitude,
                obj.location_longitude
            )
        return obj.location_address if obj.location_address else 'No location'

    location_display.short_description = 'Location'

    actions = ['mark_as_responding', 'mark_as_resolved']

    def mark_as_responding(self, request, queryset):
        updated = queryset.filter(status='active').update(status='responding')
        self.message_user(request, f'{updated} alert(s) marked as responding.')

    mark_as_responding.short_description = "Mark as responding (help on the way)"

    def mark_as_resolved(self, request, queryset):
        updated = queryset.exclude(status='resolved').update(status='resolved', resolved_by=request.user)
        self.message_user(request, f'{updated} alert(s) marked as resolved.')

    mark_as_resolved.short_description = "Mark as resolved"