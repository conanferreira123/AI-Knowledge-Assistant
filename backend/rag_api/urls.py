from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('login/', views.api_login, name='api_login'),
    path('conversations/', views.list_conversations, name='list_conversations'),
    path('conversations/create/', views.create_conversation, name='create_conversation'),
    path('conversations/<int:conversation_id>/history/',views.conversation_history,name='conversation_history'),
    path('conversations/<int:conversation_id>/upload/',views.upload_document,name='upload_document'),
    path('conversations/<int:conversation_id>/chat/',views.chat_api,name='chat_api')
]