import os
import logging
from typing import Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import requests
import json

logging.basicConfig(level=logging.INFO)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "chroma_store"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Gemini Studio API token from environment

embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
vectordb = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embed_model)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def query_gemini_model(prompt: str) -> str:
    """
    Call Gemini API with the provided prompt and return the raw content response.
    """
    logging.info("Starting Gemini API call...")
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {  # Added generationConfig for proper response management
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "responseMimeType": "application/json"
        }
    }
    logging.debug(f"Gemini API Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    logging.info("Gemini API call completed.")

    if "candidates" in data and len(data["candidates"]) > 0:
        content = data["candidates"][0].get("content", "")
        # If content is a string, return it directly
        if isinstance(content, str):
            return content
        # If content is a dict with 'parts', concatenate text parts
        if isinstance(content, dict) and "parts" in content:
            return "".join(part.get("text", "") for part in content["parts"])
        # Otherwise, convert to string as fallback
        return str(content)
    return ""


def generate_grounded_test_cases(user_query: str, top_k: int = 5) -> Optional[str]:
    """
    Retrieve relevant documents and generate grounded test cases from Gemini API.

    Args:
        user_query: The user query string describing test case needs.
        top_k: Number of top relevant docs to retrieve.

    Returns:
        JSON string of generated test cases.
    """
    retriever = vectordb.as_retriever(search_kwargs={"k": top_k})

    # Updated method usage: consider switching to invoke() in future LangChain versions
    try:
        relevant_docs = retriever.get_relevant_documents(user_query)
    except AttributeError:
        # fallback or migration path if get_relevant_documents deprecated
        relevant_docs = retriever.invoke(user_query)  # Adjust this based on actual LangChain version

    context = "\n\n".join(doc.page_content for doc in relevant_docs)

    if not GEMINI_API_KEY:
        logging.info("GEMINI_API_KEY not found: using mock test case output")
        return """
        [
          {
            "Test_ID": "TC-001",
            "Title": "Apply valid discount code SAVE15",
            "Description": "Verify total price reduces by 15% when valid code is applied.",
            "Grounded_In": ["product_specs.md"]
          }
        ]
        """

    prompt = (
        "You are an expert QA test case generator.\n"
        "Create structured test cases with IDs, titles, descriptions, and source document references.\n"
        "Use ONLY the following documentation context:\n\n"
        f"{context}\n\n"
        f"User query:\n{user_query}\n\n"
        "Respond ONLY with well-formed JSON."
    )

    try:
        return query_gemini_model(prompt)
    except Exception as e:
        logging.error(f"Error generating test cases: {e}")
        return None
