from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import Message, Conversation
from users.models import UserConnection
from django.views.decorators.http import require_http_methods


@login_required
def messages_view(request):

    user = request.user


    try:
        profile = user.userprofile
    except:
        profile = None

    conversations = Conversation.objects.filter(
        participants=user
    ).select_related().prefetch_related('participants', 'participants__userprofile').order_by('-updated_at')


    conversations_with_users = []
    for conversation in conversations:
        other_user = conversation.get_other_participant(user)
        if other_user:

            last_message = Message.objects.filter(
                Q(sender=user, recipient=other_user) |
                Q(sender=other_user, recipient=user)
            ).order_by('-timestamp').first()


            unread_count = Message.objects.filter(
                sender=other_user,
                recipient=user,
                is_read=False
            ).count()

            conversations_with_users.append({
                'conversation': conversation,
                'other_user': other_user,
                'last_message': last_message,
                'unread_count': unread_count,
            })

    context = {
        'conversations': conversations_with_users,
        'user': user,
        'profile': profile,
    }
    return render(request, 'chat/messages.html', context)


@login_required
def conversation_detail(request, conversation_id):

    user = request.user

    conversation = get_object_or_404(Conversation, id=conversation_id, participants=user)
    other_user = conversation.get_other_participant(user)


    message_list = Message.objects.filter(
        Q(sender=user, recipient=other_user) |
        Q(sender=other_user, recipient=user)
    ).order_by('timestamp')


    unread_messages = Message.objects.filter(
        recipient=user,
        sender=other_user,
        is_read=False
    )
    for msg in unread_messages:
        msg.mark_as_seen()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')

        if content:
            Message.objects.create(
                conversation=conversation,
                sender=user,
                recipient=other_user,
                content=content,
                message_type='text'
            )
        elif image:
            Message.objects.create(
                conversation=conversation,
                sender=user,
                recipient=other_user,
                image=image,
                message_type='image'
            )
        elif file:
            Message.objects.create(
                conversation=conversation,
                sender=user,
                recipient=other_user,
                file=file,
                message_type='file'
            )

        conversation.updated_at = timezone.now()
        conversation.save()
        return redirect('chat:conversation_detail', conversation_id=conversation_id)

    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': message_list,
    }
    return render(request, 'chat/conversation_detail.html', context)
@login_required
def start_conversation(request, user_id):

    user = request.user

    other_user = get_object_or_404(User, pk=user_id)


    is_connected = UserConnection.objects.filter(
        Q(from_user=user, to_user=other_user, status='connected') |
        Q(from_user=other_user, to_user=user, status='connected')
    ).exists()

    if not is_connected:
        messages.error(request, 'You must be connected to message this user.')
        return redirect('community')


    conversation = Conversation.objects.filter(participants=user).filter(participants=other_user).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(user, other_user)

    return redirect('chat:conversation_detail', conversation_id=conversation.id)


@login_required
def send_message_ajax(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    user = request.user

    conversation = get_object_or_404(Conversation, id=conversation_id, participants=user)
    other_user = conversation.get_other_participant(user)

    try:
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')

        if not content and not image:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        message_type = 'image' if image else 'text'

        message = Message.objects.create(
            sender=user,
            recipient=other_user,
            content=content if content else None,
            image=image,
            message_type=message_type
        )

        conversation.updated_at = timezone.now()
        conversation.save()

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'sender': message.sender.first_name,
                'content': message.content,
                'image': message.image.url if message.image else None,
                'message_type': message.message_type,
                'timestamp': message.timestamp.strftime('%b %d, %H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@login_required
@require_http_methods(["GET"])
def get_unread_count(request, conversation_id):

    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=user)
    other_user = conversation.get_other_participant(user)


    unread_count = Message.objects.filter(
        sender=other_user,
        recipient=user,
        is_read=False
    ).count()

    return JsonResponse({
        'conversation_id': conversation_id,
        'unread_count': unread_count
    })



@login_required
@require_http_methods(["GET"])
def check_seen_status(request, conversation_id):

    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=user)
    other_user = conversation.get_other_participant(user)


    my_messages = Message.objects.filter(
        sender=user,
        recipient=other_user,
        conversation=conversation
    ).values('id', 'is_read', 'seen_at')

    seen_data = {}
    for msg in my_messages:
        seen_data[msg['id']] = {
            'is_read': msg['is_read'],
            'seen_at': msg['seen_at'].isoformat() if msg['seen_at'] else None
        }

    return JsonResponse({'messages': seen_data})