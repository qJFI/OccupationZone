from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

def apply_to_freelancer_job(job_link, resume_path, labels, freelancer_email, freelancer_password):
    driver = webdriver.Chrome()
    try:
        # 1. Log in to Freelancer
        driver.get("https://www.freelancer.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "emailOrUsernameInput").send_keys(freelancer_email)
        driver.find_element(By.ID, "passwordInput").send_keys(freelancer_password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        # 2. Go to the job link
        driver.get(job_link)
        time.sleep(3)

        # 3. Click 'Bid on this Project'
        try:
            bid_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Bid on this Project')]")
            bid_btn.click()
            time.sleep(2)
        except NoSuchElementException:
            return False, "Bid button not found"

        # 4. Fill out bid amount, period, and cover letter if present
        try:
            bid_amount = driver.find_element(By.NAME, "bidAmount")
            bid_amount.clear()
            bid_amount.send_keys(labels.get('salary_expectations', ''))
        except NoSuchElementException:
            pass

        try:
            period = driver.find_element(By.NAME, "period")
            period.clear()
            period.send_keys(labels.get('availability', ''))
        except NoSuchElementException:
            pass

        try:
            cover_letter = driver.find_element(By.NAME, "bidDescription")
            cover_letter.clear()
            cover_letter.send_keys(labels.get('overview', ''))
        except NoSuchElementException:
            pass

        # 5. Submit bid
        try:
            submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Place Bid')]")
            submit_btn.click()
            time.sleep(2)
            return True, "Applied successfully!"
        except NoSuchElementException:
            return False, "Place Bid button not found"

    except Exception as e:
        return False, str(e)
    finally:
        driver.quit() 