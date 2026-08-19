from django.db import transaction

from rag_api.models import Document, DocumentChunk
from rag_engine.ingestion import ingest_file


@transaction.atomic
def index_document(document: Document):
    """
    Index an uploaded document.

    UPDATED WORKFLOW:
    1. Mark document as processing.
    2. Run ingestion pipeline and store vectors in Chroma.
    3. Remove any previous chunks for re-indexing.
    4. Save fresh DocumentChunk rows in SQLite.
    5. Mark document as indexed.
    6. Return the indexed document.
    """

    # ------------------------------------------------------------------
    # 1. Mark processing
    # ------------------------------------------------------------------
    document.status = 'processing'
    document.save(update_fields=['status'])

    try:
        # ------------------------------------------------------------------
        # 2. Run ingestion.
        #
        # IMPORTANT:
        # We pass conversation_id so Chroma stores conversation metadata.
        # This is required for conversation-scoped retrieval.
        # ------------------------------------------------------------------
        chunks = ingest_file(
            file_path=document.file.path,
            document_id=document.id,
            conversation_id=document.conversation.id,
        )

        # ------------------------------------------------------------------
        # 3. Remove any previous chunks before re-indexing.
        # This keeps SQLite consistent when a document is reprocessed.
        # ------------------------------------------------------------------
        DocumentChunk.objects.filter(document=document).delete()

        chunk_objects = []

        for i, chunk in enumerate(chunks):
            metadata = chunk.metadata or {}

            content = chunk.page_content.strip()

            # ------------------------------------------------------------------
            # 4. Store chunks in SQLite.
            #
            # chunk_index matches the metadata stored in Chroma so we can
            # trace vectors back to database rows later.
            # ------------------------------------------------------------------
            chunk_objects.append(
                DocumentChunk(
                    document=document,
                    chunk_index=i,
                    content=content,
                    token_count=len(content.split()),  # simple token estimate
                    page_number=metadata.get('page'),
                )
            )

        # Bulk insert chunks for efficiency
        DocumentChunk.objects.bulk_create(chunk_objects)

        # ------------------------------------------------------------------
        # 5. Update document statistics and mark as indexed.
        # ------------------------------------------------------------------
        document.page_count = len(
            set(
                c.page_number
                for c in chunk_objects
                if c.page_number is not None
            )
        )

        document.status = 'indexed'
        document.save(update_fields=['page_count', 'status'])

        return document

    except Exception:
        # ------------------------------------------------------------------
        # If anything fails during ingestion or chunk creation, mark the
        # document as failed so the UI can show the correct status.
        # ------------------------------------------------------------------
        document.status = 'failed'
        document.save(update_fields=['status'])
        raise