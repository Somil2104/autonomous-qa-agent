import requests
import os
import logging
import json
import re
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract the FIRST valid JSON object from text, even if extra content exists.
    """
    # Match the first JSON block using a robust regex pattern for balanced braces
    match = re.search(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)
    if not match:
        return {"actions": [], "assertions": []}

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"actions": [], "assertions": []}

def call_gemini_api(test_case_title: str, test_case_description: str) -> Dict[str, Any]:
    """
    Call Gemini API and return structured JSON (actions + assertions).
    """
    if not api_key:
        logging.warning("GEMINI_API_KEY is not set.")
        return {"actions": [], "assertions": []}

    prompt_text = f"""
You are a QA test case generator.

Generate a STRICT JSON object with two keys:
- "actions": list of action objects,
- "assertions": list of assertion objects.

Rules:
- Return ONLY valid JSON (UTF-8).
- NO markdown.
- NO text outside JSON.
- NO explanations.
- If unsure, return: {{"actions": [], "assertions": []}}

Test case title: {test_case_title}
Test case description: {test_case_description}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.9,
            "repetition_penalty": 1.0,
            "max_output_tokens": 1024,
            "responseMimeType": "application/json"
        }
    }

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Gemini API call failed: {e}")
        return {"actions": [], "assertions": []}

    try:
        data = response.json()
    except json.JSONDecodeError:
        logging.error("Gemini response is not valid JSON.")
        return {"actions": [], "assertions": []}

    candidates = data.get("candidates", [])
    if not candidates:
        return {"actions": [], "assertions": []}

    content = candidates[0].get("content", "")
    raw_text = ""

    if isinstance(content, dict) and "parts" in content:
        raw_text = "".join(part.get("text", "") for part in content["parts"])
    else:
        raw_text = str(content)

    return extract_json(raw_text)

def generate_selenium_script(
    test_case: str,
    html_code: str,
    base_url: Optional[str] = "http://localhost:8501"
) -> str:
    """
    Generate Selenium test script using Gemini structured output.
    """

    try:
        gemini_response = call_gemini_api(test_case, html_code)
    except Exception as e:
        logging.warning(f"Gemini API call failed: {e}")
        gemini_response = {"actions": [], "assertions": []}

    script = [
        "import logging",
        "from selenium import webdriver",
        "from selenium.webdriver.common.by import By",
        "from selenium.webdriver.support.ui import WebDriverWait",
        "from selenium.webdriver.support import expected_conditions as EC",
        "from selenium.common.exceptions import TimeoutException",
        "from selenium.webdriver.chrome.service import Service",
        "from webdriver_manager.chrome import ChromeDriverManager",
        "import time",
        "",
        "logging.basicConfig(level=logging.INFO)",
        "",
        "def test_case():",
        "    service = Service(ChromeDriverManager().install())",
        "    driver = webdriver.Chrome(service=service)",
        "    wait = WebDriverWait(driver, 10)",
        "    try:",
        f"        driver.get('{base_url}')",
        ""
    ]

    # Build actions
    for action in gemini_response.get("actions", []):
        loc_type = action.get("locator_type", "").upper()
        loc_value = action.get("locator_value", "")
        action_type = action.get("type", "")
        value = action.get("value", "")

        if not loc_type or not loc_value or not action_type:
            continue

        if action_type == "input":
            script.extend([
                "        try:",
                f"            elem = wait.until(EC.visibility_of_element_located((By.{loc_type}, '{loc_value}')))",
                "            elem.clear()",
                f"            elem.send_keys('{value}')",
                f"            logging.info('Typed \"{value}\" into {loc_type}={loc_value}')",
                "            time.sleep(2)",
                "        except TimeoutException:",
                f"            logging.error('Input element {loc_type}={loc_value} not found.')",
                ""
            ])

        elif action_type == "click":
            script.extend([
                "        try:",
                f"            elem = wait.until(EC.element_to_be_clickable((By.{loc_type}, '{loc_value}')))",
                "            elem.click()",
                f"            logging.info('Clicked {loc_type}={loc_value}')",
                "            time.sleep(2)",
                "        except TimeoutException:",
                f"            logging.error('Clickable element {loc_type}={loc_value} not found.')",
                ""
            ])

    # Build assertions
    for assertion in gemini_response.get("assertions", []):
        loc_type = assertion.get("locator_type", "").upper()
        loc_value = assertion.get("locator_value", "")
        a_type = assertion.get("type", "")
        text = assertion.get("text", "")

        if not loc_type or not loc_value or not a_type:
            continue

        if a_type == "text_present":
            script.extend([
                "        try:",
                f"            condition = wait.until(EC.text_to_be_present_in_element((By.{loc_type}, '{loc_value}'), '{text}'))",
                f"            assert condition, 'Text \"{text}\" not found in element {loc_type}={loc_value}'",
                f"            logging.info('Assertion passed: {text}')",
                "            time.sleep(2)",
                "        except Exception as e:",
                "            logging.error(f'Assertion failed: {e}')",
                ""
            ])

    # Fallback if nothing generated
    if not gemini_response.get("actions") and not gemini_response.get("assertions"):
        script.append("        # No actions/assertions generated by Gemini. Add steps manually here.\n")

    # Closing block
    script.extend([
        "    finally:",
        "        driver.quit()",
        "",
        "if __name__ == '__main__':",
        "    test_case()",
    ])

    return "\n".join(script)
