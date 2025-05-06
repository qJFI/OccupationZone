from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

def apply_to_linkedin_job(job_link, resume_path, labels, linkedin_email, linkedin_password):
    driver = webdriver.Chrome()
    try:
        # 1. Log in to LinkedIn
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(linkedin_email)
        driver.find_element(By.ID, "password").send_keys(linkedin_password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        # 2. Go to the job link
        driver.get(job_link)
        time.sleep(3)

        # 3. Click 'Easy Apply'
        try:
            easy_apply_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
            easy_apply_btn.click()
            time.sleep(2)
        except NoSuchElementException:
            return False, "Easy Apply button not found"

        # 4. Fill out the application form
        try:
            phone_input = driver.find_element(By.XPATH, "//input[contains(@id, 'phoneNumber')]")
            phone_input.clear()
            phone_input.send_keys(labels.get('phone', ''))
        except NoSuchElementException:
            pass

        # 5. Upload resume if upload field is present
        try:
            upload_input = driver.find_element(By.XPATH, "//input[@type='file']")
            upload_input.send_keys(resume_path)
            time.sleep(2)
        except NoSuchElementException:
            pass

        # 6. Click Next/Submit until done
        while True:
            try:
                next_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Continue to next step')]")
                next_btn.click()
                time.sleep(2)
            except NoSuchElementException:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
                    submit_btn.click()
                    time.sleep(2)
                    return True, "Applied successfully!"
                except NoSuchElementException:
                    break
        return False, "Could not complete application (no submit button found)"
    except Exception as e:
        return False, str(e)
    finally:
        driver.quit() 