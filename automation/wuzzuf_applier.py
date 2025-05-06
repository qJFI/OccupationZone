from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

def apply_to_wuzzuf_job(job_link, resume_path, labels, wuzzuf_email, wuzzuf_password):
    driver = webdriver.Chrome()
    try:
        # 1. Log in to Wuzzuf
        driver.get("https://wuzzuf.net/login")
        time.sleep(2)
        driver.find_element(By.NAME, "email").send_keys(wuzzuf_email)
        driver.find_element(By.NAME, "password").send_keys(wuzzuf_password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        # 2. Go to the job link
        driver.get(job_link)
        time.sleep(3)

        # 3. Click 'Apply'
        try:
            apply_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Apply')]")
            apply_btn.click()
            time.sleep(2)
        except NoSuchElementException:
            return False, "Apply button not found"

        # 4. Upload resume if upload field is present
        try:
            upload_input = driver.find_element(By.XPATH, "//input[@type='file']")
            upload_input.send_keys(resume_path)
            time.sleep(2)
        except NoSuchElementException:
            pass

        # 5. Fill out additional fields if needed (example: phone)
        try:
            phone_input = driver.find_element(By.XPATH, "//input[contains(@name, 'phone')]")
            phone_input.clear()
            phone_input.send_keys(labels.get('phone', ''))
        except NoSuchElementException:
            pass

        # 6. Submit application
        try:
            submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            submit_btn.click()
            time.sleep(2)
            return True, "Applied successfully!"
        except NoSuchElementException:
            return False, "Submit button not found"

    except Exception as e:
        return False, str(e)
    finally:
        driver.quit() 