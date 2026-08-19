from sentence_transformers import CrossEncoder


# ----------------------------------------------------------------------
# Cross-encoder reranker model.
#
# This model scores (query, chunk) pairs directly, which is usually much
# more accurate than embedding similarity for the final ranking step.
#
# CPU-friendly choice:
#     BAAI/bge-reranker-base
# ----------------------------------------------------------------------
_reranker = CrossEncoder('BAAI/bge-reranker-base')


def rerank(
    query: str,
    chunks: list,
    top_k: int = 5,
):
    """
    Rerank candidate chunks using a cross-encoder.

    Input:
        query: user question
        chunks: list of chunk dictionaries, each containing at least:
                {
                    'chunk_id': ...,
                    'content': '...',
                    ...
                }

    Returns:
        The same chunk dictionaries sorted by reranker score descending.

    NOTE:
    Higher reranker score = more relevant.
    """

    if not chunks:
        return []

    # ------------------------------------------------------------------
    # Build (query, document) pairs for the cross-encoder.
    # ------------------------------------------------------------------
    pairs = [
        (query, chunk['content'])
        for chunk in chunks
    ]

    # ------------------------------------------------------------------
    # Predict relevance scores.
    # ------------------------------------------------------------------
    scores = _reranker.predict(pairs)

    reranked = []

    for chunk, score in zip(chunks, scores):
        # ------------------------------------------------------------------
        # Attach reranker score for debugging and source inspection.
        # ------------------------------------------------------------------
        chunk_copy = dict(chunk)
        chunk_copy['reranker_score'] = float(score)
        reranked.append(chunk_copy)

    # ------------------------------------------------------------------
    # Sort by reranker score descending (higher is better).
    # ------------------------------------------------------------------
    reranked.sort(
        key=lambda x: x['reranker_score'],
        reverse=True,
    )

    return reranked[:top_k]


if __name__ == '__main__':
    sample_chunks = [
        {
            'chunk_id': 1,
            'content': 'Retrieval-Augmented Generation combines retrieval with generation.',
        },
        {
            'chunk_id': 2,
            'content': 'A convolutional neural network is used for image tasks.',
        },
        {
            'chunk_id': 3,
            'content': 'RAG retrieves relevant documents before answering.',
        },
    ]

    results = rerank(
        query='What is RAG?',
        chunks=sample_chunks,
        top_k=2,
    )

    for item in results:
        print('CHUNK:', item['chunk_id'])
        print('SCORE:', item['reranker_score'])
        print(item['content'])
        print('-' * 40)