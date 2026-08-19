from django.db import transaction
from django.utils import timezone

from rag_api.models import (
    Conversation,
    Message,
    MessageSource,
    DocumentChunk,
)

from rag_engine.retriever import retrieve
from rag_engine.generator import generate_answer
from rag_engine.query_rewriter import rewrite_query


# ----------------------------------------------------------------------
# Follow-up detection
# ----------------------------------------------------------------------
FOLLOWUP_WORDS = {
    'it', 'they', 'them', 'this', 'that',
    'these', 'those', 'more', 'detail',
    'details', 'explain', 'elaborate',
    'further',
}


def needs_rewrite(question: str) -> bool:
    q = question.lower()

    return (
        len(q.split()) <= 5 or
        any(word in q for word in FOLLOWUP_WORDS)
    )


# ----------------------------------------------------------------------
# Conversation history builder
# ----------------------------------------------------------------------
def build_history(conversation, max_messages=6):
    messages = conversation.messages.order_by('-created_at')[:max_messages]

    if not messages:
        return ''

    messages = list(reversed(messages))

    parts = []

    for m in messages:
        role = 'User' if m.role == 'user' else 'Assistant'
        parts.append(f'{role}: {m.content}')

    return '\n'.join(parts)


@transaction.atomic
def ask_question(
    conversation: Conversation,
    question: str,
    k: int = 8,
):
    """
    Conversational RAG workflow.

    1. Save user message.
    2. Ensure documents exist.
    3. Build recent conversation history.
    4. Rewrite follow-up questions into standalone queries.
    5. Retrieve relevant chunks.
    6. Generate grounded answer with conversational continuity.
    7. Save assistant message.
    8. Save citations.
    9. Update timestamp.
    """

    # ------------------------------------------------------------------
    # 1. Save user message
    # ------------------------------------------------------------------
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=question,
    )

    # ------------------------------------------------------------------
    # 2. Ensure documents exist
    # ------------------------------------------------------------------
    has_documents = conversation.documents.exists()

    if not has_documents:
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

    # ------------------------------------------------------------------
    # 3. Build recent conversation history
    # ------------------------------------------------------------------
    history = build_history(conversation)

    # ------------------------------------------------------------------
    # 4. Rewrite follow-up questions into standalone queries
    # ------------------------------------------------------------------
    standalone_question = question

    if history and needs_rewrite(question):
        try:
            standalone_question = rewrite_query(
                query=question,
                history=history,
            )
        except Exception as e:
            print('Query rewrite failed:', e)
            standalone_question = question

    print('Original question:', question)
    print('Standalone question:', standalone_question)

    # ------------------------------------------------------------------
    # 5. Retrieve relevant chunks
    # ------------------------------------------------------------------
    retrieved_results = retrieve(
        query=standalone_question,
        conversation_id=conversation.id,
        history=history,
        k=k,
    )

    # DEBUG: print retrieved chunks
    for i, item in enumerate(retrieved_results, 1):
        print(f'\n===== RETRIEVED CHUNK {i} =====')
        print(item['metadata'])
        print(item['content'])
        print('=' * 80)

    contexts = [
        item['content']
        for item in retrieved_results
    ]

    # ------------------------------------------------------------------
    # 6. Generate answer with history
    # ------------------------------------------------------------------
    answer_text = generate_answer(
        question=standalone_question,
        retrieved_docs=contexts,
        history=history,
    )

    # ------------------------------------------------------------------
    # 7. Save assistant message
    # ------------------------------------------------------------------
    assistant_message = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=answer_text,
    )

    sources_payload = []

    # ------------------------------------------------------------------
    # 8. Save citations
    # ------------------------------------------------------------------
    for item in retrieved_results:
        chunk_id = item.get('chunk_id')

        if chunk_id is None:
            continue

        try:
            chunk = DocumentChunk.objects.select_related(
                'document'
            ).get(id=chunk_id)

            source = MessageSource.objects.create(
                message=assistant_message,
                chunk=chunk,
                relevance_score=item.get('score', 0.0),
            )

            sources_payload.append(
                {
                    'document_id': chunk.document.id,
                    'document_title': chunk.document.title,
                    'chunk_id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'page_number': chunk.page_number,
                    'relevance_score': source.relevance_score,
                    'preview': chunk.content[:200],
                }
            )

        except DocumentChunk.DoesNotExist:
            continue

    # ------------------------------------------------------------------
    # 9. Update conversation timestamp
    # ------------------------------------------------------------------
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['updated_at'])

    return {
        'answer': answer_text,
        'message_id': assistant_message.id,
        'sources': sources_payload,
    }