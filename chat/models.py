from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    image = models.ImageField(upload_to='messages/images/', blank=True, null=True)
    file = models.FileField(upload_to='messages/files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)


    seen_at = models.DateTimeField(null=True, blank=True)

    def mark_as_seen(self):
        """Mark this message as read/seen by the recipient"""
        if not self.is_read:
            self.is_read = True
            self.seen_at = timezone.now()
            self.save()
    class Meta:
        ordering = ['timestamp']

    def str(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.content[:50] if self.content else self.message_type}"


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def str(self):
        return f"Conversation {self.id}"

    def get_other_participant(self, user):
        return self.participants.exclude(pk=user.pk).first()