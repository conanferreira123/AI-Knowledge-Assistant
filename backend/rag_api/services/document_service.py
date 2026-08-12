from django.db import transaction

from rag_api.models import Document, DocumentChunk
from rag_engine.ingestion import ingest_file


@transaction.atomic
def index_document(document: Document):
    """
    Index an uploaded document.

    Workflow:
    1. Mark document as processing.
    2. Run ingestion pipeline.
    3. Save DocumentChunk rows.
    4. Mark document as indexed.
    5. Return the indexed document.
    """

    # Mark processing
    document.status = 'processing'
    document.save(update_fields=['status'])

    try:
        # Run ingestion and get LangChain Document chunks back
        chunks = ingest_file(   #store chunks in VectorDB
            file_path=document.file.path,
            document_id=document.id,
            conversation_id=document.conversation.id,
        )

        # Remove any previous chunks for re-indexing
        DocumentChunk.objects.filter(document=document).delete()

        chunk_objects = []

        for i, chunk in enumerate(chunks):
            metadata = chunk.metadata or {}

            content = chunk.page_content.strip()
            #store chunks in SQLite DB
            chunk_objects.append(
                DocumentChunk(
                    document=document,
                    chunk_index=i,
                    content=content,
                    token_count=len(content.split()),  # simple estimate
                    page_number=metadata.get('page'),
                )
            )

        # Bulk insert chunks
        DocumentChunk.objects.bulk_create(chunk_objects)

        # Update document status
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
        document.status = 'failed'
        document.save(update_fields=['status'])
        raise