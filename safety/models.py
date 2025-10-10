from django.db import models
from django.conf import settings

# Create your models here.

class SafetyReport(models.Model):
	reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	title = models.CharField(max_length=200)
	description = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	resolved = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.title} - {'resolved' if self.resolved else 'open'}"


class SafetyGuideline(models.Model):
	"""Optional model to store guideline pages (used by safety views)."""
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=200, unique=True)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['title']

	def __str__(self):
		return self.title
