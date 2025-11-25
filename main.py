import os
import logging
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from typing import List
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse

from utils.file_utils import read_documentation_files, read_html_files
from utils.knowledge_base import build_knowledge_base
from utils.rag_generation import generate_grounded_test_cases
from utils.selenium_generator import generate_selenium_script

logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logging.info(f"GEMINI_API_KEY is set: {'Yes' if GEMINI_API_KEY else 'No'}")

app = FastAPI(title="Autonomous QA Agent")

DOCS_DIR = "uploaded_docs"
HTML_DIR = "uploaded_html"

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Autonomous QA Agent Backend is running!"}

# ---------------------- Upload Endpoints ---------------------- #
@app.post("/upload/documentation/")
async def upload_documentation(file: UploadFile = File(...)):
    file_location = os.path.join(DOCS_DIR, file.filename)
    with open(file_location, "wb") as f:
        contents = await file.read()
        f.write(contents)
    return {"filename": file.filename, "message": "Documentation uploaded successfully"}

@app.post("/upload/html/")
async def upload_html(file: UploadFile = File(...)):
    file_location = os.path.join(HTML_DIR, file.filename)
    with open(file_location, "wb") as f:
        contents = await file.read()
        f.write(contents)
    return {"filename": file.filename, "message": "HTML file uploaded successfully"}

# ---------------------- Test Case Endpoints ---------------------- #
class TestCaseRequest(BaseModel):
    user_query: str

class TestCaseResponse(BaseModel):
    test_cases: str
    status: str

@app.post("/generate-test-cases/", response_model=TestCaseResponse)
async def generate_test_cases(request: TestCaseRequest):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set")
        test_cases = generate_grounded_test_cases(request.user_query)
        # Ensure JSON serializable
        if not isinstance(test_cases, str):
            import json
            test_cases = json.dumps(test_cases, indent=2)
        return TestCaseResponse(test_cases=test_cases, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-selenium-script/")
async def get_selenium_script(test_case_title: str, test_case_description: str):
    try:
        script_content = generate_selenium_script(test_case_title, test_case_description)
        return {"selenium_script": script_content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download-selenium-script/")
async def download_selenium_script(test_case_title: str, test_case_description: str):
    try:
        script_content = generate_selenium_script(test_case_title, test_case_description)
        safe_title = test_case_title.lower().replace(" ", "_")
        filename = f"{safe_title}_selenium_test.py"

        # Use tempfile to avoid /tmp issues
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
            tmp_file.write(script_content.encode())
            filepath = tmp_file.name

        return FileResponse(
            path=filepath,
            media_type="application/x-python-code",
            filename=filename
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------------- Knowledge Base ---------------------- #
@app.post("/build-knowledge-base/")
async def build_kb_endpoint(
    documentation_filenames: List[str] = Body(...), 
    html_filenames: List[str] = Body(...)
):
    try:
        docs_text = []

        # Load documentation files
        for filename in documentation_filenames:
            filepath = os.path.join(DOCS_DIR, filename)
            logging.info(f"Loading documentation file: {filepath} (exists: {os.path.exists(filepath)})")
            if not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail=f"Documentation file not found: {filename}")
            text = read_documentation_files([filename])
            docs_text.append({"text": text, "source": filename})

        # Load HTML files
        for filename in html_filenames:
            filepath = os.path.join(HTML_DIR, filename)
            logging.info(f"Loading HTML file: {filepath} (exists: {os.path.exists(filepath)})")
            if not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail=f"HTML file not found: {filename}")
            text = read_html_files([filename])
            docs_text.append({"text": text, "source": filename})

        vectordb = build_knowledge_base(docs_text)

        # Get number of vectors safely
        vector_count = getattr(vectordb._collection, "count", lambda: 0)()

        return {
            "status": "success",
            "doc_count": len(docs_text),
            "vector_count": vector_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
