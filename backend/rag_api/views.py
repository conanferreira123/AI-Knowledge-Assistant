from django.shortcuts import render
from django.contrib.auth import authenticate, login
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rag_api.models import Conversation, Document
from rag_api.services.document_service import index_document
from rag_api.services.chat_service import ask_question

def ensure_guest_session(request):
    """
    Ensure the browser has a Django session key.
    Django creates one automatically if it does not exist.
    """
    if not request.session.session_key:
        request.session.create()

@api_view(['POST'])
def api_login(request):
    """
    Handle user login and return an authentication token.
    """
    # Your logic for handling user login goes here
    # For example, you might want to authenticate the user and return a token
    
    try:
        data=json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON."}, status=400)

    username=data.get('username')
    password=data.get('password')
    user=authenticate(username=username,password=password)
    if user is None:
        return JsonResponse({'success':False,'message': 'Invalid credentials'}, status=400)
    return JsonResponse({'success': True, 'message': 'Login successful!'},status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_document(request, conversation_id):
    """
    Upload a document to a conversation and index it.
    """

    if request.user.is_authenticated:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=request.user,
        )
    else:
        ensure_guest_session(request)

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=None,
            guest_session_key=request.session.session_key,
        )
        
    uploaded_file = request.data.get('file')

    if not uploaded_file:
        return JsonResponse(
            {'success': False, 'message': 'No document uploaded.'},
            status=400,
        )

    document = Document.objects.create(
        conversation=conversation,
        title=request.data.get('title', uploaded_file.name),
        file=uploaded_file,
        file_type=request.data.get(
            'file_type',
            uploaded_file.content_type,
        ),
        status='uploaded',
    )

    try:
        index_document(document)

        return JsonResponse(
            {
                'success': True,
                'document': {
                    'id': document.id,
                    'title': document.title,
                    'status': document.status,
                    'page_count': document.page_count,
                },
            },
            status=201,
        )

    except Exception as e:
        return JsonResponse(
            {'success': False, 'message': str(e)},
            status=500,
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def create_conversation(request):
    if request.user.is_authenticated:
        conversation = Conversation.objects.create(
            owner=request.user,
            title='New Chat'
        )
    else:
        ensure_guest_session(request)
        conversation = Conversation.objects.create(
            owner=None, 
            guest_session_key=request.session.session_key, 
            title='Guest Chat' 
        )
        

    return JsonResponse({
        'id': conversation.id,
        'title': conversation.title,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def list_conversations(request):
    if request.user.is_authenticated:
        conversations = Conversation.objects.filter(
            owner=request.user
        )
    else:
        ensure_guest_session(request)

        conversations = Conversation.objects.filter(
            owner=None,
            guest_session_key=request.session.session_key,
        )

    data = [
        {
            'id': c.id,
            'title': c.title,
        }
        for c in conversations
    ]

    return JsonResponse({'conversations': data})

@api_view(['GET'])
@permission_classes([AllowAny])
def conversation_history(request, conversation_id):
    if request.user.is_authenticated:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=request.user,
        )
    else:
        ensure_guest_session(request)

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=None,
            guest_session_key=request.session.session_key,
        )

    messages_data = []

    for message in conversation.messages.all():
        sources_data = []

        for source in message.sources.all():
            chunk = source.chunk

            sources_data.append({
                'document_id': chunk.document.id,
                'document_title': chunk.document.title,
                'chunk_id': chunk.id,
                'chunk_index': chunk.chunk_index,
                'page_number': chunk.page_number,
                'relevance_score': source.relevance_score,
                'preview': chunk.content[:200],
            })

        messages_data.append({
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'sources': sources_data,
        })

    documents_data = [
        {
            'id': doc.id,
            'title': doc.title,
            'status': doc.status,
            'page_count': doc.page_count,
        }
        for doc in conversation.documents.all()
    ]

    return JsonResponse({
        'conversation_id': conversation.id,
        'title': conversation.title,
        'messages': messages_data,
        'documents': documents_data,
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def chat_api(request, conversation_id):
    """
    Ask a question about documents in a conversation.
    Supports both authenticated users and guests.
    """

    # 1. Load conversation
    if request.user.is_authenticated:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=request.user,
        )
    else:
        ensure_guest_session(request)

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=None,
            guest_session_key=request.session.session_key,
        )

    # 2. Read message from request body
    message = request.data.get('message')

    if not message or not str(message).strip():
        return JsonResponse(
            {
                'success': False,
                'message': 'Message is required.',
            },
            status=400,
        )

    try:
        # 3. Process chat
        result = ask_question(
            conversation=conversation,
            question=message.strip(),
        )

        # 4. Return response
        return JsonResponse(
            {
                'success': True,
                'conversation_id': conversation.id,
                'message_id': result['message_id'],
                'answer': result['answer'],
                'sources': result['sources'],
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                'success': False,
                'message': 'Failed to process chat request.',
                'error': str(e),
            },
            status=500,
        )