from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / 'documents'
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


def split_documents(documents):     #split documents into chunks
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


_embeddings = HuggingFaceEmbeddings(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
)

_vectordb = Chroma(
    persist_directory=str(VECTORSTORE_DIR),
    embedding_function=_embeddings,
)


def load_and_split_pdf(file_path: str):
    """
    Load a PDF document and split it into text chunks.
    """
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return split_documents(documents)


def delete_document_vectors(document_id: int):
    """
    Remove existing Chroma vectors for a document_id before re-indexing.
    Prevents duplicate vectors and dangling metadata.
    """
    try:
        _vectordb._collection.delete(where={'document_id': document_id})
        _vectordb.persist()
    except Exception as e:
        print(f"Notice: Chroma collection delete for document_id={document_id}: {e}")


def store_chunks_in_chroma(chunks: list):
    """
    Persist chunks with complete metadata (including chunk_id) into Chroma.
    """
    _vectordb.add_documents(chunks)
    _vectordb.persist()


def ingest_file(file_path: str, document_id: int, conversation_id: int):
    """
    Legacy single-file ingestion helper.
    """
    chunks = load_and_split_pdf(file_path)

    for i, chunk in enumerate(chunks):
        chunk.metadata['document_id'] = document_id
        chunk.metadata['conversation_id'] = conversation_id
        chunk.metadata['chunk_index'] = i

    delete_document_vectors(document_id)
    store_chunks_in_chroma(chunks)

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

