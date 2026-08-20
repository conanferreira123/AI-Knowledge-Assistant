from django.db import transaction

from rag_api.models import Document, DocumentChunk
from rag_engine.ingestion import (
    load_and_split_pdf,
    delete_document_vectors,
    store_chunks_in_chroma,
)


@transaction.atomic
def index_document(document: Document):
    """
    Index an uploaded document.

    UPDATED CANONICAL WORKFLOW:
    1. Mark document as processing.
    2. Load PDF and split text into chunks.
    3. Remove previous DocumentChunk rows in SQLite for this document.
    4. Save fresh DocumentChunk rows in SQLite to generate primary keys (chunk_id).
    5. Delete previous Chroma vectors for this document_id (re-indexing safety).
    6. Attach SQLite chunk_id and metadata to each chunk.
    7. Store chunks with complete metadata (including chunk_id) in Chroma.
    8. Update document statistics and mark as indexed.
    9. Return the indexed document.
    """

    # ------------------------------------------------------------------
    # 1. Mark processing
    # ------------------------------------------------------------------
    document.status = 'processing'
    document.save(update_fields=['status'])

    try:
        # ------------------------------------------------------------------
        # 2. Load PDF and split into text chunks
        # ------------------------------------------------------------------
        chunks = load_and_split_pdf(document.file.path)

        # ------------------------------------------------------------------
        # 3. Remove previous chunks in SQLite before re-indexing
        # ------------------------------------------------------------------
        DocumentChunk.objects.filter(document=document).delete()

        # ------------------------------------------------------------------
        # 4. Save fresh DocumentChunk rows in SQLite to generate chunk IDs
        # ------------------------------------------------------------------
        chunk_objects = []

        for i, chunk in enumerate(chunks):
            metadata = chunk.metadata or {}
            content = chunk.page_content.strip()

            chunk_objects.append(
                DocumentChunk(
                    document=document,
                    chunk_index=i,
                    content=content,
                    token_count=len(content.split()),
                    page_number=metadata.get('page'),
                )
            )

        DocumentChunk.objects.bulk_create(chunk_objects)

        # Fetch newly created DB records ordered by chunk_index to get generated primary keys (id)
        saved_db_chunks = list(
            DocumentChunk.objects.filter(document=document).order_by('chunk_index')
        )

        # ------------------------------------------------------------------
        # 5. Delete previous Chroma vectors for this document (prevents duplicates)
        # ------------------------------------------------------------------
        delete_document_vectors(document.id)

        # ------------------------------------------------------------------
        # 6. Assign canonical metadata (including chunk_id = db_chunk.id)
        # ------------------------------------------------------------------
        for chunk, db_chunk in zip(chunks, saved_db_chunks):
            chunk.metadata['chunk_id'] = db_chunk.id
            chunk.metadata['document_id'] = document.id
            chunk.metadata['conversation_id'] = document.conversation.id
            chunk.metadata['chunk_index'] = db_chunk.chunk_index
            chunk.metadata['page'] = db_chunk.page_number

        # ------------------------------------------------------------------
        # 7. Store vectors in Chroma with complete metadata
        # ------------------------------------------------------------------
        store_chunks_in_chroma(chunks)

        # ------------------------------------------------------------------
        # 8. Update document statistics and mark as indexed
        # ------------------------------------------------------------------
        document.page_count = len(
            set(
                c.page_number
                for c in saved_db_chunks
                if c.page_number is not None
            )
        )

        document.status = 'indexed'
        document.save(update_fields=['page_count', 'status'])

        return document

    except Exception:
        # Mark document as failed if indexing errors out
        document.status = 'failed'
        document.save(update_fields=['status'])
        raise