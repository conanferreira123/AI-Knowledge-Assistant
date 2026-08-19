from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from rag_api.models import Conversation, Document
from rag_api.services.document_service import index_document
from rag_api.services.chat_service import ask_question


# ==================================================
# Guest session configuration
# ==================================================

GUEST_QUERY_LIMIT = 3

# Redis/cache lifetime for a guest session.
#
# This is intentionally longer than a normal browsing
# session so that the guest conversation can survive
# normal page navigation/reloads.
#
# Django's session expiration is controlled separately.
GUEST_STATE_TIMEOUT = 60 * 60 * 24


# ==================================================
# CSRF
# ==================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_api(request):
    """
    Ensure that Django sends a CSRF cookie to the browser.

    React calls this endpoint before making
    CSRF-protected POST requests.
    """

    return JsonResponse({
        'success': True
    })


# ==================================================
# Guest session helpers
# ==================================================

def ensure_guest_session(request):
    """
    Ensure that the browser has a Django session key.

    The session ID itself is stored in the browser as
    Django's HttpOnly sessionid cookie.

    Guest-specific state is stored in Redis through
    Django's cache interface.
    """

    if not request.session.session_key:
        request.session.create()

    return request.session.session_key


def guest_cache_key(session_key):
    """
    Return the Redis/cache key used for a guest session.
    """

    return f'guest_session:{session_key}'


def get_guest_state(request):
    """
    Retrieve guest state from Redis.

    Returns None if no guest state exists.
    """

    session_key = request.session.session_key

    if not session_key:
        return None

    return cache.get(
        guest_cache_key(session_key)
    )


def set_guest_state(
    request,
    conversation_id,
    query_count=0,
):
    """
    Store guest state in Redis.
    """

    session_key = ensure_guest_session(request)

    cache.set(
        guest_cache_key(session_key),
        {
            'conversation_id': conversation_id,
            'query_count': query_count,
        },
        timeout=GUEST_STATE_TIMEOUT,
    )


def clear_guest_state(request):
    """
    Remove guest state from Redis.
    """

    session_key = request.session.session_key

    if not session_key:
        return

    cache.delete(
        guest_cache_key(session_key)
    )


def get_guest_conversation(request):
    """
    Return the single conversation belonging to the
    current guest session.

    The conversation ID stored in Redis is treated as
    the authoritative guest conversation reference.

    We additionally verify the conversation in SQLite
    using the Django session key.
    """

    state = get_guest_state(request)

    if not state:
        return None

    conversation_id = state.get(
        'conversation_id'
    )

    if not conversation_id:
        return None

    session_key = request.session.session_key

    return Conversation.objects.filter(
        id=conversation_id,
        owner=None,
        guest_session_key=session_key,
    ).first()


# ==================================================
# Guest session start
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def start_guest_session(request):
    """
    Start a guest session.

    A guest session receives exactly ONE conversation.

    If the current guest session already has a conversation,
    that conversation is returned instead of creating another.

    Redis stores:

        conversation_id
        query_count

    The Django session ID remains in the browser's
    HttpOnly sessionid cookie.
    """

    # --------------------------------------------------
    # Authenticated users do not need guest sessions.
    # --------------------------------------------------

    if request.user.is_authenticated:

        return JsonResponse(
            {
                'success': False,
                'message': 'User is already authenticated.',
            },
            status=400,
        )

    # --------------------------------------------------
    # Ensure Django session exists.
    # --------------------------------------------------

    session_key = ensure_guest_session(request)

    # --------------------------------------------------
    # Check whether a guest conversation already exists.
    # --------------------------------------------------

    existing_conversation = get_guest_conversation(
        request
    )

    if existing_conversation:

        state = get_guest_state(request)

        query_count = (
            state.get('query_count', 0)
            if state
            else 0
        )

        # Refresh Redis state in case it expired.
        set_guest_state(
            request,
            existing_conversation.id,
            query_count=query_count,
        )

        return JsonResponse({
            'success': True,
            'conversation_id': existing_conversation.id,
            'title': existing_conversation.title,
            'query_count': query_count,
            'query_limit': GUEST_QUERY_LIMIT,
        })

    # --------------------------------------------------
    # Create exactly ONE guest conversation.
    # --------------------------------------------------

    conversation = Conversation.objects.create(
        owner=None,
        guest_session_key=session_key,
        title='New Chat',
    )

    # --------------------------------------------------
    # Store guest state in Redis.
    # --------------------------------------------------

    set_guest_state(
        request,
        conversation.id,
        query_count=0,
    )

    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id,
        'title': conversation.title,
        'query_count': 0,
        'query_limit': GUEST_QUERY_LIMIT,
    })


# ==================================================
# Authentication
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    Register a new user account.

    Registration does not automatically log the user in.
    The user must log in separately.
    """

    data = request.data

    username = data.get(
        'username',
        ''
    ).strip()

    email = data.get(
        'email',
        ''
    ).strip()

    password = data.get(
        'password',
        ''
    )

    if not username or not email or not password:

        return JsonResponse(
            {
                'success': False,
                'message': (
                    'Username, email and password '
                    'are required.'
                ),
            },
            status=400,
        )

    if User.objects.filter(
        username=username
    ).exists():

        return JsonResponse(
            {
                'success': False,
                'message': (
                    'Username already exists.'
                ),
            },
            status=400,
        )

    if User.objects.filter(
        email=email
    ).exists():

        return JsonResponse(
            {
                'success': False,
                'message': (
                    'An account with this email '
                    'already exists.'
                ),
            },
            status=400,
        )

    if len(password) < 8:

        return JsonResponse(
            {
                'success': False,
                'message': (
                    'Password must be at least '
                    '8 characters long.'
                ),
            },
            status=400,
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )

    return JsonResponse(
        {
            'success': True,
            'message': 'Registration successful.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
        },
        status=201,
    )


# ==================================================
# Login
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    Authenticate a user and create a Django session.

    If the browser currently owns a guest conversation,
    that conversation is migrated to the authenticated user.

    This means the user can continue the exact same chat
    after logging in.

    The conversation's:

        messages
        documents
        document chunks
        message sources

    all remain intact because they already reference
    the same Conversation record.
    """

    data = request.data

    username_input = data.get(
        'username'
    ) or data.get('email')

    password = data.get(
        'password'
    )

    if not username_input or not password:

        return JsonResponse(
            {
                'success': False,
                'message': (
                    'Username/email and password '
                    'are required.'
                ),
            },
            status=400,
        )

    # Support login via email or username
    user_obj = User.objects.filter(email=username_input).first()
    target_username = user_obj.username if user_obj else username_input

    user = authenticate(
        username=target_username,
        password=password,
    )

    if user is None:

        return JsonResponse(
            {
                'success': False,
                'message': 'Invalid credentials',
            },
            status=400,
        )

    # --------------------------------------------------
    # Capture the guest conversation BEFORE login.
    #
    # After login(), request.user becomes the authenticated
    # user and session key is cycled, so we must store
    # the old_session_key first.
    # --------------------------------------------------

    guest_conversation = None
    old_session_key = request.session.session_key

    if old_session_key:

        guest_conversation = get_guest_conversation(
            request
        )

    # --------------------------------------------------
    # Authenticate the Django session.
    # --------------------------------------------------

    login(
        request,
        user,
    )

    # --------------------------------------------------
    # Migrate guest conversation to user.
    # --------------------------------------------------

    migrated_conversation_id = None

    if guest_conversation and old_session_key:

        # Security check:
        #
        # The conversation must still be an anonymous
        # conversation belonging to this exact session key.
        if (
            guest_conversation.owner is None
            and guest_conversation.guest_session_key == old_session_key
        ):

            guest_conversation.owner = user
            guest_conversation.guest_session_key = None

            guest_conversation.save(
                update_fields=[
                    'owner',
                    'guest_session_key',
                ]
            )

            migrated_conversation_id = (
                guest_conversation.id
            )

    # --------------------------------------------------
    # Guest state is no longer needed after migration.
    # --------------------------------------------------

    clear_guest_state(request)

    return JsonResponse(
        {
            'success': True,
            'message': 'Login successful!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'migrated_conversation_id':
                migrated_conversation_id,
        },
        status=200,
    )


# ==================================================
# Current user
# ==================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def me_api(request):
    """
    Return the currently authenticated user.

    Django determines request.user from the sessionid
    cookie automatically.
    """

    if request.user.is_authenticated:

        return JsonResponse(
            {
                'authenticated': True,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                },
            }
        )

    return JsonResponse(
        {
            'authenticated': False
        }
    )


# ==================================================
# Logout
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_logout(request):
    """
    Log the user out and destroy the current Django
    authentication session.
    """

    logout(request)

    return JsonResponse(
        {
            'success': True,
            'message': 'Logout successful.',
        }
    )


# ==================================================
# Document upload
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_document(
    request,
    conversation_id,
):
    """
    Upload a document to a conversation and index it.

    Authenticated users can access conversations that
    belong to them.

    Guests can access only the single conversation
    belonging to their guest session.
    """

    if request.user.is_authenticated:

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=request.user,
        )

    else:

        ensure_guest_session(request)

        state = get_guest_state(request)

        if not state:

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'Guest session has not been started.'
                    ),
                },
                status=403,
            )

        if state.get(
            'conversation_id'
        ) != conversation_id:

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'Guests can only upload documents '
                        'to their active conversation.'
                    ),
                },
                status=403,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=None,
            guest_session_key=request.session.session_key,
        )

    uploaded_file = request.data.get(
        'file'
    )

    if not uploaded_file:

        return JsonResponse(
            {
                'success': False,
                'message': 'No document uploaded.',
            },
            status=400,
        )

    document = Document.objects.create(
        conversation=conversation,
        title=request.data.get(
            'title',
            uploaded_file.name,
        ),
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
            {
                'success': False,
                'message': str(e),
            },
            status=500,
        )


# ==================================================
# Conversation creation
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def create_conversation(request):
    """
    Create a conversation.

    Authenticated users can create unlimited conversations.

    Guests cannot create additional conversations.

    Guest conversations are created exclusively through
    /api/guest/start/.
    """

    # --------------------------------------------------
    # Authenticated user
    # --------------------------------------------------

    if request.user.is_authenticated:

        conversation = Conversation.objects.create(
            owner=request.user,
            title='New Chat',
        )

        return JsonResponse(
            {
                'id': conversation.id,
                'title': conversation.title,
            }
        )

    # --------------------------------------------------
    # Guest
    # --------------------------------------------------

    return JsonResponse(
        {
            'success': False,
            'message': (
                'Guests cannot create new conversations. '
                'Please log in to create another chat.'
            ),
            'login_required': True,
        },
        status=403,
    )


# ==================================================
# Conversation list
# ==================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_conversations(request):
    """
    Return conversations belonging to the authenticated
    user.

    Guests receive only their single active conversation.
    """

    if request.user.is_authenticated:

        conversations = Conversation.objects.filter(
            owner=request.user
        )

    else:

        state = get_guest_state(request)

        if not state:

            return JsonResponse(
                {
                    'conversations': []
                }
            )

        conversation_id = state.get(
            'conversation_id'
        )

        conversations = Conversation.objects.filter(
            id=conversation_id,
            owner=None,
            guest_session_key=request.session.session_key,
        )

    data = [
        {
            'id': conversation.id,
            'title': conversation.title,
        }
        for conversation in conversations
    ]

    return JsonResponse(
        {
            'conversations': data
        }
    )


# ==================================================
# Conversation history
# ==================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def conversation_history(
    request,
    conversation_id,
):
    """
    Return messages and documents belonging to a
    conversation.

    Guests may access only their single guest conversation.
    """

    if request.user.is_authenticated:

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=request.user,
        )

    else:

        state = get_guest_state(request)

        if not state:

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'Guest session has not been started.'
                    ),
                },
                status=403,
            )

        if state.get(
            'conversation_id'
        ) != conversation_id:

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'You cannot access this conversation.'
                    ),
                },
                status=403,
            )

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

            sources_data.append(
                {
                    'document_id':
                        chunk.document.id,

                    'document_title':
                        chunk.document.title,

                    'chunk_id':
                        chunk.id,

                    'chunk_index':
                        chunk.chunk_index,

                    'page_number':
                        chunk.page_number,

                    'relevance_score':
                        source.relevance_score,

                    'preview':
                        chunk.content[:200],
                }
            )

        messages_data.append(
            {
                'id': message.id,
                'role': message.role,
                'content': message.content,
                'created_at':
                    message.created_at.isoformat(),
                'sources': sources_data,
            }
        )

    documents_data = [
        {
            'id': document.id,
            'title': document.title,
            'status': document.status,
            'page_count': document.page_count,
        }
        for document in conversation.documents.all()
    ]

    response = {
        'conversation_id':
            conversation.id,

        'title':
            conversation.title,

        'messages':
            messages_data,

        'documents':
            documents_data,
    }

    # --------------------------------------------------
    # Include guest query information.
    # --------------------------------------------------

    if not request.user.is_authenticated:

        state = get_guest_state(request)

        if state:

            response[
                'query_count'
            ] = state.get(
                'query_count',
                0,
            )

            response[
                'query_limit'
            ] = GUEST_QUERY_LIMIT

    return JsonResponse(response)


# ==================================================
# Chat
# ==================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def chat_api(
    request,
    conversation_id,
):
    """
    Ask a question about documents in a conversation.

    Authenticated users:
        Unlimited queries.

    Guests:
        Maximum of GUEST_QUERY_LIMIT successful queries.

    The guest query count is stored server-side in Redis.
    React state is NOT authoritative.
    """

    # --------------------------------------------------
    # 1. Load conversation
    # --------------------------------------------------

    guest_state = None

    if request.user.is_authenticated:

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=request.user,
        )

    else:

        guest_state = get_guest_state(request)

        if not guest_state:

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'Guest session has not been started.'
                    ),
                    'guest_session_required': True,
                },
                status=403,
            )

        if guest_state.get(
            'conversation_id'
        ) != conversation_id:

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'You can only use your guest '
                        'conversation.'
                    ),
                },
                status=403,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            owner=None,
            guest_session_key=request.session.session_key,
        )

        # --------------------------------------------------
        # 2. Enforce guest query limit
        # --------------------------------------------------

        query_count = guest_state.get(
            'query_count',
            0,
        )

        if query_count >= GUEST_QUERY_LIMIT:

            return JsonResponse(
                {
                    'success': False,
                    'guest_limit_reached': True,
                    'query_count': query_count,
                    'query_limit': GUEST_QUERY_LIMIT,
                    'message': (
                        'You have used all three '
                        'free queries. Please log in '
                        'to continue.'
                    ),
                },
                status=403,
            )

    # --------------------------------------------------
    # 3. Read message
    # --------------------------------------------------

    message = request.data.get(
        'message'
    )

    if (
        not message
        or not str(message).strip()
    ):

        return JsonResponse(
            {
                'success': False,
                'message': 'Message is required.',
            },
            status=400,
        )

    clean_message = str(
        message
    ).strip()

    # --------------------------------------------------
    # 4. Rename conversation
    # --------------------------------------------------

    if conversation.title in [
        'New Chat',
        'Guest Chat',
    ]:

        title = ' '.join(
            clean_message.split()
        )[:60]

        conversation.title = (
            title.capitalize()
        )

        conversation.save(
            update_fields=[
                'title'
            ]
        )

    # --------------------------------------------------
    # 5. Process chat
    # --------------------------------------------------

    try:

        result = ask_question(
            conversation=conversation,
            question=clean_message,
        )

        # --------------------------------------------------
        # 6. Increment guest query count ONLY after
        # successful processing.
        # --------------------------------------------------

        if not request.user.is_authenticated:

            current_state = get_guest_state(
                request
            )

            if current_state:

                current_count = current_state.get(
                    'query_count',
                    0,
                )

                current_state[
                    'query_count'
                ] = current_count + 1

                cache.set(
                    guest_cache_key(
                        request.session.session_key
                    ),
                    current_state,
                    timeout=GUEST_STATE_TIMEOUT,
                )

                query_count = (
                    current_count + 1
                )

            else:

                query_count = 1

        else:

            query_count = None

        # --------------------------------------------------
        # 7. Return response
        # --------------------------------------------------

        response = {
            'success': True,

            'conversation_id':
                conversation.id,

            'message_id':
                result['message_id'],

            'answer':
                result['answer'],

            'sources':
                result['sources'],

            'title':
                conversation.title,
        }

        if not request.user.is_authenticated:

            response[
                'query_count'
            ] = query_count

            response[
                'query_limit'
            ] = GUEST_QUERY_LIMIT

            response[
                'remaining_queries'
            ] = max(
                GUEST_QUERY_LIMIT
                - query_count,
                0,
            )

        return JsonResponse(
            response,
            status=200,
        )

    except Exception as e:

        return JsonResponse(
            {
                'success': False,
                'message': (
                    'Failed to process '
                    'chat request.'
                ),
                'error': str(e),
            },
            status=500,
        )