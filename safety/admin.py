from django.contrib import admin
from .models import SafetyReport


@admin.register(SafetyReport)
class SafetyReportAdmin(admin.ModelAdmin):
	list_display = ('title', 'reporter', 'created_at', 'resolved')
	list_filter = ('resolved', 'created_at')
	search_fields = ('title', 'description', 'reporter__username')


from .models import SafetyGuideline


@admin.register(SafetyGuideline)
class SafetyGuidelineAdmin(admin.ModelAdmin):
	list_display = ('title', 'slug', 'created_at')
	prepopulated_fields = {'slug': ('title',)}
