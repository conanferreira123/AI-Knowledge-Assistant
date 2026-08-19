from django.urls import path

from rag_api.views import (
    csrf_api,
    register_api,
    api_login,
    api_logout,
    me_api,

    start_guest_session,

    upload_document,

    create_conversation,
    list_conversations,
    conversation_history,

    chat_api,
)


urlpatterns = [

    # ==================================================
    # CSRF
    # ==================================================

    path(
        'csrf/',
        csrf_api,
        name='csrf',
    ),


    # ==================================================
    # Authentication
    # ==================================================

    path(
        'register/',
        register_api,
        name='register',
    ),

    path(
        'login/',
        api_login,
        name='login',
    ),

    path(
        'logout/',
        api_logout,
        name='logout',
    ),

    path(
        'me/',
        me_api,
        name='me',
    ),


    # ==================================================
    # Guest session
    # ==================================================

    path(
        'guest/start/',
        start_guest_session,
        name='guest-start',
    ),


    # ==================================================
    # Conversations
    # ==================================================

    path(
        'conversations/create/',
        create_conversation,
        name='create-conversation',
    ),

    path(
        'conversations/',
        list_conversations,
        name='list-conversations',
    ),

    path(
        'conversations/<int:conversation_id>/history/',
        conversation_history,
        name='conversation-history',
    ),


    # ==================================================
    # Documents
    # ==================================================

    path(
        'conversations/<int:conversation_id>/upload/',
        upload_document,
        name='upload-document',
    ),


    # ==================================================
    # Chat
    # ==================================================

    path(
        'conversations/<int:conversation_id>/chat/',
        chat_api,
        name='chat',
    ),
]