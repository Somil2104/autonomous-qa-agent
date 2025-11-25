import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"  # Adjust if backend is elsewhere

st.title("Autonomous QA Agent")

# --- 1. Upload files ---
st.header("1. Upload Documents and HTML")

uploaded_docs = st.file_uploader(
    "Upload support document files (MD, TXT, JSON, PDF, etc.)",
    type=["md", "txt", "json", "pdf"],
    accept_multiple_files=True
)
uploaded_html = st.file_uploader(
    "Upload checkout.html file",
    type=["html"]
)

if st.button("Upload Selected Files"):
    if (not uploaded_docs or len(uploaded_docs) == 0) and not uploaded_html:
        st.warning("Please select files to upload.")
    else:
        files_to_upload = (uploaded_docs if uploaded_docs else []) + ([uploaded_html] if uploaded_html else [])
        for file in files_to_upload:
            files = {'file': (file.name, file.getvalue())}  # Correct getvalue() casing
            url = f"{BACKEND_URL}/upload/html/" if file.name.endswith(".html") else f"{BACKEND_URL}/upload/documentation/"
            try:
                with st.spinner(f"Uploading {file.name}..."):
                    response = requests.post(url, files=files)
                if response.ok:
                    st.success(f"Uploaded {file.name}")
                else:
                    st.error(f"Failed to upload {file.name}: {response.text}")
            except Exception as e:
                st.error(f"Error uploading {file.name}: {str(e)}")

# --- 2. Build knowledge base ---
st.header("2. Build Knowledge Base")

if st.button("Build Knowledge Base"):
    doc_filenames = [f.name for f in uploaded_docs] if uploaded_docs else []
    html_filenames = [uploaded_html.name] if uploaded_html else []

    st.write("Documentation filenames to send:", doc_filenames)
    st.write("HTML filenames to send:", html_filenames)

    if not doc_filenames and not html_filenames:
        st.warning("Upload some documents and/or the HTML file first!")
    else:
        payload = {"documentation_filenames": doc_filenames, "html_filenames": html_filenames}
        try:
            with st.spinner("Building knowledge base..."):
                resp = requests.post(f"{BACKEND_URL}/build-knowledge-base/", json=payload, timeout=120)
            if resp.ok:
                data = resp.json()
                st.success(f"Knowledge base built with {data.get('doc_count')} documents, {data.get('vector_count')} vectors.")
            else:
                st.error(f"Failed to build knowledge base: {resp.text}")
        except Exception as e:
            st.error(f"Error building knowledge base: {str(e)}")

# --- 3. Generate test cases ---
st.header("3. Generate Test Cases")

query = st.text_area("Enter test case generation query (e.g., 'Generate all positive and negative test cases for the discount code feature.')")

if st.button("Generate Test Cases"):
    if not query.strip():
        st.warning("Please enter a valid query.")
    else:
        try:
            with st.spinner("Generating test cases..."):
                resp = requests.post(f"{BACKEND_URL}/generate-test-cases/", json={"user_query": query}, timeout=120)
            if resp.ok:
                test_cases = resp.json().get("test_cases", "")
                st.text_area("Generated Test Cases (JSON or text):", value=test_cases, height=300)

                # Store generated test cases in session state for step 4
                st.session_state.generated_test_cases = test_cases
            else:
                st.error(f"Failed to generate test cases: {resp.text}")
        except Exception as e:
            st.error(f"Error generating test cases: {str(e)}")

# --- 4. Generate Selenium scripts ---
st.header("4. Generate Selenium Script from Test Case")

if 'generated_test_cases' not in st.session_state or not st.session_state.generated_test_cases:
    st.info("Generate test cases first to select one.")
else:
    test_case_title = st.text_input("Test Case Title (copy from generated test cases)")
    test_case_description = st.text_area("Test Case Description (copy from generated test cases)")

    if st.button("Generate Selenium Script"):
        if not test_case_title.strip() or not test_case_description.strip():
            st.warning("Please provide both title and description of a selected test case.")
        else:
            try:
                with st.spinner("Generating Selenium script..."):
                    params = {"test_case_title": test_case_title, "test_case_description": test_case_description}
                    resp = requests.get(f"{BACKEND_URL}/generate-selenium-script/", params=params, timeout=120)
                if resp.ok:
                    script = resp.json().get("selenium_script", "")
                    st.code(script, language="python")
                else:
                    st.error(f"Failed to generate Selenium script: {resp.text}")
            except Exception as e:
                st.error(f"Error generating Selenium script: {str(e)}")
