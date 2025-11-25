# utils/knowledge_base.py

import os
import logging
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

def build_knowledge_base(
    documents: List[Dict[str, str]],  # Each dict with {"text": str, "source": str}
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

    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)

        texts = []
        metadatas = []

        for doc in documents:
            chunks = splitter.split_text(doc["text"])
            texts.extend(chunks)
            metadatas.extend([{"source_document": doc["source"]}] * len(chunks))

        embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        os.makedirs(persist_dir, exist_ok=True)

        vectordb = Chroma(persist_directory=persist_dir, embedding_function=embed_model)

        vectordb.add_texts(texts=texts, metadatas=metadatas)
        vectordb.persist()

        logger.info(f"Knowledge base built and saved with {len(texts)} text chunks.")
        return vectordb

    except Exception as e:
        logger.error(f"Error building knowledge base: {e}")
        raise e


# Example usage
if __name__ == "__main__":
    docs = [
        {"text": "Discount codes reduce price by set percentages.", "source": "product_specs.md"},
        {"text": "The UI shows error messages in red text.", "source": "ui_ux_guide.txt"},
        # Add your other docs here...
    ]

    vector_store = build_knowledge_base(docs)
    print(f"Vector store built and persisted with {len(vector_store)} vectors.")
