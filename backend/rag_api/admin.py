from django.contrib import admin

from .models import (
    Document,
    DocumentChunk,
    Conversation,
    Message,
    MessageSource,
)

admin.site.register(Document)
admin.site.register(DocumentChunk)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(MessageSource)