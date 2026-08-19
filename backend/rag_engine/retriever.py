from rag_api.models import DocumentChunk
from .retriever_dense import dense_retrieve
from .retriever_sparse import sparse_retrieve
from .fusion import rrf_fusion
from .reranker import rerank


def retrieve(
    query: str,
    conversation_id: int,
    history: str = '',
    k: int = 5,
):
    """
    Main hybrid retrieval pipeline.

    FINAL PIPELINE:
    1. Dense retrieval from Chroma.
    2. Sparse BM25 retrieval from SQLite.
    3. Reciprocal Rank Fusion (RRF).
    4. Load canonical chunks from SQLite.
    5. Validate conversation ownership.
    6. Cross-encoder reranking.
    7. Return top-k chunks.

    Parameters
    ----------
    query:
        Standalone query produced by chat_service.
    conversation_id:
        Current conversation scope.
    history:
        Conversation history (currently unused here, but kept for future
        retrieval improvements such as history-aware reranking).
    k:
        Number of final chunks to return.

    Returns
    -------
    list[dict]
        Final reranked chunks.
    """

    # ------------------------------------------------------------------
    # IMPORTANT:
    # The query has ALREADY been rewritten in chat_service.py using
    # conversation history. Do NOT rewrite it again here.
    # ------------------------------------------------------------------
    rewritten_query = query

    print('Retrieval query:', rewritten_query)

    # ------------------------------------------------------------------
    # 1. Dense semantic retrieval.
    # ------------------------------------------------------------------
    dense_results = dense_retrieve(
        query=rewritten_query,
        conversation_id=conversation_id,
        k=50,
    )

    # ------------------------------------------------------------------
    # 2. Sparse BM25 retrieval.
    # ------------------------------------------------------------------
    sparse_results = sparse_retrieve(
        query=rewritten_query,
        conversation_id=conversation_id,
        k=50,
    )

    # ------------------------------------------------------------------
    # 3. Fuse rankings using RRF.
    # ------------------------------------------------------------------
    fused = rrf_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
    )

    candidate_ids = [
        item['chunk_id']
        for item in fused[:30]
    ]

    if not candidate_ids:
        return []

    # ------------------------------------------------------------------
    # 4. Load canonical chunks from SQLite.
    # ------------------------------------------------------------------
    chunk_map = {
        chunk.id: chunk
        for chunk in DocumentChunk.objects.filter(
            id__in=candidate_ids
        ).select_related('document')
    }

    candidate_chunks = []

    for item in fused[:10]:
        chunk_id = item['chunk_id']

        chunk = chunk_map.get(chunk_id)

        if chunk is None:
            continue

        # ------------------------------------------------------------------
        # 5. Safety check: prevent cross-conversation leakage.
        # ------------------------------------------------------------------
        if chunk.document.conversation_id != conversation_id:
            continue

        candidate_chunks.append(
            {
                'chunk_id': chunk.id,
                'content': chunk.content,
                'metadata': {
                    'document_id': chunk.document.id,
                    'conversation_id': conversation_id,
                    'chunk_index': chunk.chunk_index,
                    'page': chunk.page_number,
                    'document_title': chunk.document.title,
                },
                'score': item['fused_score'],
            }
        )

    if not candidate_chunks:
        return []

    # ------------------------------------------------------------------
    # 6. Cross-encoder reranking.
    # ------------------------------------------------------------------
    reranked = rerank(
        query=rewritten_query,
        chunks=candidate_chunks,
        top_k=k,
    )

    # ------------------------------------------------------------------
    # 7. Return final top-k chunks.
    # ------------------------------------------------------------------
    return reranked


if __name__ == '__main__':
    results = retrieve(
        query='What is RAG?',
        conversation_id=1,
        k=3,
    )

    for item in results:
        print('CHUNK ID:', item['chunk_id'])
        print('FUSED SCORE:', item['score'])
        print('RERANKER SCORE:', item['reranker_score'])
        print(item['content'][:120])
        print('-' * 40)