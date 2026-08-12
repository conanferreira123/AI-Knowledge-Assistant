from django.db import transaction
from django.utils import timezone
from rag_api.models import (Conversation,Message,MessageSource,DocumentChunk)
from rag_engine.retriever import retrieve
from rag_engine.generator import generate_answer


@transaction.atomic
def ask_question(conversation: Conversation,question: str,k: int = 4):
    """
    Process a user question for a conversation.

    Workflow:
    1. Save user message.
    2. Get active document IDs for the conversation.
    3. Retrieve relevant chunks from Chroma.
    4. Generate answer with the LLM.
    5. Save assistant message.
    6. Save source citations.
    7. Update conversation timestamp.
    8. Return response payload.
    """

    # 1. Save user message
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=question,
    )

    # 2. Get document IDs attached to this conversation
    document_ids = list(
        conversation.documents.values_list('id', flat=True)
    )

    if not document_ids:
        answer_text = (
            'No documents are attached to this conversation. '
            'Please upload a document first.'
        )

        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=answer_text,
        )

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

        return {
            'answer': answer_text,
            'message_id': assistant_message.id,
            'sources': [],
        }

    # 3. Retrieve relevant chunks
    retrieved_results = retrieve(
        query=question,
        document_ids=document_ids,
        k=k,
    )

    contexts = [
        item['content']
        for item in retrieved_results
    ]

    # 4. Generate answer
    answer_text = generate_answer(question, contexts)

    # 5. Save assistant message
    assistant_message = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=answer_text,
    )

    sources_payload = []

    # 6. Save source citations
    for item in retrieved_results:
        metadata = item.get('metadata', {})

        document_id = metadata.get('document_id')
        chunk_index = metadata.get('chunk_index')

        if document_id is None or chunk_index is None:
            continue

        try:
            chunk = DocumentChunk.objects.get(
                document_id=document_id,
                chunk_index=chunk_index,
            )

            source = MessageSource.objects.create(
                message=assistant_message,
                chunk=chunk,
                relevance_score=metadata.get('score', 0.0),
            )

            sources_payload.append(
                {
                    'document_id': document_id,
                    'document_title': chunk.document.title,
                    'chunk_id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'page_number': chunk.page_number,
                    'relevance_score': source.relevance_score,
                    'preview': chunk.content[:200],
                }
            )

        except DocumentChunk.DoesNotExist:
            # Vector exists but DB chunk row is missing; skip safely.
            continue

    # 7. Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['updated_at'])

    # 8. Return payload
    return {
        'answer': answer_text,
        'message_id': assistant_message.id,
        'sources': sources_payload,
    }