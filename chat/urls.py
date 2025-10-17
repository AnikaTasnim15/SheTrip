from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('messages/', views.messages_view, name='messages'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('api/send/<int:conversation_id>/', views.send_message_ajax, name='send_message_ajax'),
path('api/check-seen/<int:conversation_id>/', views.check_seen_status, name='check_seen_status'),
]