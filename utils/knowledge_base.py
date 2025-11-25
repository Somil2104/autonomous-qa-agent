# utils/knowledge_base.py

import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from typing import List, Dict

def build_knowledge_base(
    documents: List[Dict[str, str]],  # List of dicts with {"text": str, "source": str}
    persist_dir: str = "chroma_store"
) -> Chroma:
    """
    Build a vector database knowledge base by chunking and embedding document texts.

    Args:
        documents: List of documents, where each doc is a dict with:
            - 'text': the document text content
            - 'source': the source filename or descriptor to keep metadata
        persist_dir: Directory path to persist Chroma vector store.

    Returns:
        Chroma vector store instance with persisted embeddings and metadata.
    """

    # 1. Prepare text chunks and metadata per document
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)

    texts = []
    metadatas = []

    for doc in documents:
        chunks = splitter.split_text(doc["text"])
        texts.extend(chunks)
        metadatas.extend([{"source_document": doc["source"]}] * len(chunks))

    # 2. Load embedding model
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 3. Ensure persistence directory exists
    os.makedirs(persist_dir, exist_ok=True)

    # 4. Initialize or load Chroma vector store
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embed_model)

    # 5. Add texts with metadata to the vector store
    vectordb.add_texts(texts=texts, metadatas=metadatas)

    # 6. Persist vector store to disk
    vectordb.persist()

    return vectordb

# Example usage:
if __name__ == "__main__":
    docs = [
        {"text": "Discount codes reduce price by set percentages.", "source": "product_specs.md"},
        {"text": "The UI shows error messages in red text.", "source": "ui_ux_guide.txt"},
        # Add your other docs here...
    ]

    vectordb = build_knowledge_base(docs)
    print(f"Vector store built and persisted with {len(vectordb)} vectors.")
