from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# Use an absolute path so Django can find the vectorstore reliably
BASE_DIR = Path(__file__).resolve().parent
VECTORSTORE_DIR = BASE_DIR / 'vectorstore'


# Load the same embedding model used during ingestion
_embeddings = HuggingFaceEmbeddings(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
)


# Load the persisted Chroma database
_vectordb = Chroma(
    persist_directory=str(VECTORSTORE_DIR),
    embedding_function=_embeddings,
)


def retrieve(query: str, document_ids: list, k: int = 5):
    """
    Retrieve the top-k most relevant document chunks for a query,
    restricted to a specific conversation.

    Returns:
    [
        {
            'content': '...',
            'metadata': {...}
        },
        ...
    ]
    """

    docs = _vectordb.similarity_search(
        query=query,
        k=k,
        filter={'document_id': {'$in': document_ids}},
    )

    results = []

    for doc in docs:
        results.append(
            {
                'content': doc.page_content,
                'metadata': doc.metadata,
            }
        )

    return results


if __name__ == '__main__':
    retrieved = retrieve('What is Generative AI?', document_ids=[1], k=3)
    print(retrieved)