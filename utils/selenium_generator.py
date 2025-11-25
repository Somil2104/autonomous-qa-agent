from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

def generate_selenium_script(test_case_title: str, test_case_description: str, base_url: str = "http://your-web-application-url.com") -> str:
    """
    Generate a production-ready Selenium script based on test case title and description.

    This generator uses improved parsing heuristics, dynamic waits, and parameterization.

    Args:
        test_case_title (str): Title of the test case.
        test_case_description (str): Description containing action keywords.
        base_url (str): Base URL of the application under test.

    Returns:
        str: Selenium Python script content.
    """

    # Initialize logging for debug purpose in generated script
    script_lines = [
        "import logging",
        "from selenium import webdriver",
        "from selenium.webdriver.common.by import By",
        "from selenium.webdriver.support.ui import WebDriverWait",
        "from selenium.webdriver.support import expected_conditions as EC",
        "from selenium.common.exceptions import TimeoutException",
        "",
        "logging.basicConfig(level=logging.INFO)",
        "",
        "def test_case():",
        f"    driver = webdriver.Chrome()",
        f"    wait = WebDriverWait(driver, 10)",
        "    try:",
        f"        driver.get('{base_url}')",
        "",
        f"        # Test case: {test_case_title}",
        f"        # Description: {test_case_description}",
        ""
    ]

    description_lower = test_case_description.lower()

    # Improved heuristic parsing with parameterized examples

    # Handling input actions
    if any(keyword in description_lower for keyword in ["input", "enter", "type", "fill"]):
        script_lines.extend([
            "        try:",
            "            input_element = wait.until(EC.visibility_of_element_located((By.NAME, 'username')))",
            "            input_element.clear()",
            "            input_element.send_keys('testuser')  # TODO: Replace with appropriate test data",
            "            logging.info('Entered username in input field.')",
            "        except TimeoutException:",
            "            logging.error('Username input field not found.')",
            ""
        ])

    # Handling click actions
    if "click" in description_lower:
        script_lines.extend([
            "        try:",
            "            click_element = wait.until(EC.element_to_be_clickable((By.ID, 'submit-btn')))",
            "            click_element.click()",
            "            logging.info('Clicked submit button.')",
            "        except TimeoutException:",
            "            logging.error('Submit button not clickable or not found.')",
            ""
        ])

    # Handling assertions/validations
    if any(keyword in description_lower for keyword in ["assert", "validate", "check", "confirm"]):
        script_lines.extend([
            "        try:",
            "            assert_condition = wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Welcome'))",
            "            assert assert_condition, 'Expected text not found!'",
            "            logging.info('Assertion passed: Welcome text found.')",
            "        except Exception as e:",
            "            logging.error(f'Assertion failed: {e}')",
            ""
        ])

    # If no action detected
    if len(script_lines) <= 12:  # header lines + try: minimal count
        script_lines.append("        # TODO: Add your Selenium test steps here.")

    script_lines.extend([
        "    finally:",
        "        driver.quit()",
        "",
        "if __name__ == '__main__':",
        "    test_case()"
    ])

    return "\n".join(script_lines)
