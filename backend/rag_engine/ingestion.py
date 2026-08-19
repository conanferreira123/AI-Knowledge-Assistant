from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data' / 'docs'
VECTORSTORE_DIR = BASE_DIR / 'vectorstore'


def load_documents():
    documents = []

    pdf_files = list(DATA_DIR.glob('*.pdf'))

    if not pdf_files:
        print(f'No PDF files found in {DATA_DIR.resolve()}')
        return documents

    for pdf_path in pdf_files:
        print(f'Loading: {pdf_path.name}')
        loader = PyPDFLoader(str(pdf_path))
        documents.extend(loader.load())

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=200,
        separators=['\n\n', '\n', ' ', ''],
    )

    return splitter.split_documents(documents)


def build_vectorstore(chunks):
    print('Loading embedding model...')

    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )

    print('Creating Chroma vector store...')

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTORSTORE_DIR),
    )

    vectordb.persist()

    print(f'Vector store saved to: {VECTORSTORE_DIR}')


def ingest_file(file_path: str, document_id: int, conversation_id: int):
    """
    Ingest a single uploaded PDF into Chroma.

    IMPORTANT:
    We now store conversation_id in vector metadata so retrieval can be
    restricted to a single chat/conversation. This prevents cross-chat
    leakage even if old vectors still exist in Chroma.
    """

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    chunks = split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )

    vectordb = Chroma(
        persist_directory=str(VECTORSTORE_DIR),
        embedding_function=embeddings,
    )

    for i, chunk in enumerate(chunks):
        # ------------------------------------------------------------------
        # NEW: Store document_id, conversation_id and chunk_index in metadata.
        # These fields are used later by the hybrid retriever and the
        # conversation-level security filter.
        # ------------------------------------------------------------------
        chunk.metadata['document_id'] = document_id
        chunk.metadata['conversation_id'] = conversation_id
        chunk.metadata['chunk_index'] = i

    vectordb.add_documents(chunks)
    vectordb.persist()

    return chunks


def main():
    documents = load_documents()

    if not documents:
        return

    chunks = split_documents(documents)

    print(f'Loaded {len(documents)} pages')
    print(f'Created {len(chunks)} chunks')

    build_vectorstore(chunks)

    print('Ingestion complete.')


if __name__ == '__main__':
    main()