import os
import requests
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "chroma_store"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Hugging Face API token from environment
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
vectordb = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embed_model)

def query_hf_model(payload: dict) -> str:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    output = response.json()
    if isinstance(output, list) and len(output) > 0 and "generated_text" in output[0]:
        return output[0]["generated_text"]
    return str(output)

def generate_grounded_test_cases(user_query: str, top_k: int = 5) -> str:
    # Retrieve top_k relevant document chunks
    retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
    relevant_docs = retriever.get_relevant_documents(user_query)
    context = "\n\n".join(doc.page_content for doc in relevant_docs)

    # If no token, serve mock data for dev/demo
    if not HF_API_TOKEN:
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

    # Construct prompt for real API call
    prompt = (
        "You are an expert QA test case generator.\n"
        "Create structured test cases with IDs, titles, descriptions, and source document references.\n"
        "Use ONLY the following documentation context:\n\n"
        f"{context}\n\n"
        f"User query:\n{user_query}\n\n"
        "Respond ONLY with well-formed JSON."
    )
    payload = {"inputs": prompt}
    return query_hf_model(payload)
