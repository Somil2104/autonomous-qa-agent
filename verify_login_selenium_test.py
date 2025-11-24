from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def test_case():
    driver = webdriver.Chrome()
    try:
        driver.get("http://your-web-application-url.com")

        # Test case: Verify login
        # Description: Check user can input username and click submit and assert welcome

        # Example input action
        driver.find_element(By.NAME, "username").send_keys("testuser")
        # Example click action
        driver.find_element(By.ID, "submit-btn").click()
        # Example assertion
        assert "Welcome" in driver.page_source

        time.sleep(2)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_case()
