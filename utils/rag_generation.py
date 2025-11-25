import os
import logging
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "chroma_store"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Gemini Studio API token from environment

embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
vectordb = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embed_model)

# Updated Gemini official API endpoint as per Gemini 3 Developer Guide
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent"

def query_gemini_model(prompt: str) -> str:
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
        "temperature": 1.0,
        "candidateCount": 1,
        "topP": 1,
        "topK": 40,
        "maxOutputTokens": 1024,
        "stopSequences": [],
        # You can optionally add thinking_level and other parameters here per docs
        # "thinkingLevel": "high",
    }
    response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    logging.info("Gemini API call completed.")
    # Extract generated text from response structure
    if "candidates" in data and len(data["candidates"]) > 0:
        return data["candidates"][0].get("content", "")
    return ""

def generate_grounded_test_cases(user_query: str, top_k: int = 5) -> str:
    retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
    relevant_docs = retriever.get_relevant_documents(user_query)
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
        logging.error(f"Gemini API call failed: {e}")
        raise
