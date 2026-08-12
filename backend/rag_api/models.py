from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('indexed', 'Indexed'),
        ('failed', 'Failed'),
    ]

    conversation = models.ForeignKey(
        'Conversation',     #one conversation-->many documents
        on_delete=models.CASCADE,
        related_name='documents'
    )

    title = models.CharField(max_length=255)

    file = models.FileField(upload_to='documents/')

    file_type = models.CharField(max_length=20)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded'
    )

    page_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.title} (Conversation{self.conversation.id})'


class DocumentChunk(models.Model):
    document = models.ForeignKey(   #one document-->many chunks
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )

    chunk_index = models.PositiveIntegerField()

    content = models.TextField()

    token_count = models.PositiveIntegerField(default=0)

    page_number = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'chunk_index')
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f'Chunk {self.chunk_index} - {self.document.title}'


class Conversation(models.Model):
    guest_session_key = models.CharField( max_length=40, null=True, blank=True, db_index=True, )
    owner = models.ForeignKey(
        User,       #one user-->multiple conversations
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255, default='New Chat')

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        username = self.owner.username if self.owner else 'guest'
        return f'{self.title} ({username})'


class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        Conversation,   #one conversation-->many messages
        on_delete=models.CASCADE,
        related_name='messages'
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role} message in {self.conversation.title}'


class MessageSource(models.Model):
    message = models.ForeignKey(
        Message,    #one message-->many message sources
        on_delete=models.CASCADE,
        related_name='sources'
    )

    chunk = models.ForeignKey(
        DocumentChunk,  #one chunk-->many message sources
        on_delete=models.CASCADE,
        related_name='message_sources'
    )

    relevance_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('message', 'chunk')

    def __str__(self):
        return (
            f'Source: Message {self.message.id} '
            f'-> Chunk {self.chunk.id}'
        )