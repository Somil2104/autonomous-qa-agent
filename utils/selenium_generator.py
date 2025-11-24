from selenium.webdriver.common.by import By

def generate_selenium_script(test_case_title: str, test_case_description: str) -> str:
    """
    Generate a Selenium script based on simple keyword parsing of description.
    Currently supports input, click, and assert keywords.

    Args:
        test_case_title (str): Title of the test case.
        test_case_description (str): Description containing action keywords.

    Returns:
        str: Selenium Python script content.
    """

    actions_code = []

    description_lower = test_case_description.lower()

    # Basic parsing examples - extend as needed
    if "input" in description_lower or "enter" in description_lower:
        actions_code.append(
            '        # Example input action\n'
            '        driver.find_element(By.NAME, "username").send_keys("testuser")\n'
        )
    if "click" in description_lower:
        actions_code.append(
            '        # Example click action\n'
            '        driver.find_element(By.ID, "submit-btn").click()\n'
        )
    if "assert" in description_lower or "validate" in description_lower or "check" in description_lower:
        actions_code.append(
            '        # Example assertion\n'
            '        assert "Welcome" in driver.page_source\n'
        )

    # Combine actions into one string
    actions_str = "".join(actions_code) or '        # TODO: Add your Selenium test steps here.\n'

    script = f"""\
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_case():
    driver = webdriver.Chrome()
    try:
        driver.get("http://your-web-application-url.com")

        # Test case: {test_case_title}
        # Description: {test_case_description}

{actions_str}
        # Consider replacing fixed waits with explicit waits for better reliability
        # For example, use WebDriverWait for element visibility or page readiness
    finally:
        driver.quit()

if __name__ == "__main__":
    test_case()
"""
    return script
