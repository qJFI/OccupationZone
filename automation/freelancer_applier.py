from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='freelancer_applier.log')
logger = logging.getLogger(__name__)

def apply_to_freelancer_job(job_link, resume_path, labels, freelancer_email, freelancer_password, debug_mode=False):
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        logger.info(f"Starting application process for {job_link}")
        driver.get("https://www.freelancer.com/login")
        time.sleep(3)
        driver.find_element(By.ID, "emailOrUsernameInput").send_keys(freelancer_email)
        driver.find_element(By.ID, "passwordInput").send_keys(freelancer_password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        logger.info("Submitted login form")
        time.sleep(5)
        driver.get(job_link)
        time.sleep(5)
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, {i * 1000});")
            time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        # Try to find the Place Bid button using the exact HTML structure
        logger.info("Looking for Place Bid button (specific XPath)")
        place_bid_xpath = "//div[contains(@class,'BidFormBtn')]//fl-button[@fltrackinglabel='PlaceBidButton']//button[contains(@class,'ButtonElement') and contains(normalize-space(.), 'Place Bid')]"
        try:
            submit_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, place_bid_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(1)
            submit_btn.click()
            logger.info("Clicked Place Bid button (specific XPath)")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Place Bid button not found with specific XPath: {e}")
            return False, "Place Bid button not found."
        # Continue as before (fill bid, description, etc.)
        # 5. Fill out bid amount and period if present
        logger.info("Looking for bid amount field")
        time.sleep(2)
        # Bid amount
        try:
            bid_amount = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "bidAmount"))
            )
            logger.info("Found bid amount field")
            bid_amount.clear()
            bid_amount.send_keys(labels.get('salary_expectations', '50'))
            logger.info(f"Entered bid amount: {labels.get('salary_expectations', '50')}")
            time.sleep(1)
        except TimeoutException:
            logger.warning("Bid amount field not found")
        except Exception as e:
            logger.error(f"Unexpected error filling bid amount: {e}")
        # Period (days to complete project)
        try:
            period = driver.find_element(By.NAME, "period")
            logger.info("Found period field")
            period.clear()
            period.send_keys(labels.get('availability', '1'))
            logger.info(f"Entered period: {labels.get('availability', '1')}")
            time.sleep(1)
        except NoSuchElementException:
            logger.warning("Period field not found")
        except Exception as e:
            logger.error(f"Unexpected error filling period: {e}")
        # 6. Fill out the description with the fixed text
        description_text = """I'm a seasoned software developer with a strong track record delivering clean, scalable, and well-documented solutions across web, mobile, automation, and game development projects. Whether you need a custom app, API integration, dynamic frontend, full-stack system, or an engaging, well-optimized game (2D/3D, simulation, or multiplayer), I focus on understanding your vision first—then translating it into fast, reliable, and maintainable code. I bring not just technical skills, but clarity, creative problem-solving, and long-term thinking to every project. If you're looking for someone who can build with both logic and imagination, let's hop on a quick 15-minute call to align on your goals and see how I can help move things forward."""
        logger.info("Looking for description textarea")
        time.sleep(2)
        # Try to find the description field using the exact attributes provided
        description_field_found = False
        try:
            logger.info("Trying to find description field using exact attributes")
            description_field = driver.find_element(
                By.XPATH, 
                "//textarea[@class='TextArea' and contains(@class, 'ng-trigger-shakeAnimation') and @placeholder='What makes you the best candidate for this project?']"
            )
            logger.info("Found description field with exact attributes")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", description_field)
            time.sleep(1)
            description_field.click()
            time.sleep(0.5)
            description_field.clear()
            time.sleep(0.5)
            for character in description_text:
                description_field.send_keys(character)
                time.sleep(0.005)
            logger.info("Entered description text character by character")
            description_field_found = True
        except Exception as e:
            logger.error(f"Failed with exact attributes: {str(e)}")
            try:
                logger.info("Trying to find description field by ID")
                description_field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "descriptionTextArea"))
                )
                description_field.clear()
                description_field.send_keys(description_text)
                logger.info("Found and filled description field by ID")
                description_field_found = True
            except Exception as e:
                logger.info(f"ID method failed: {str(e)}")
            if not description_field_found:
                logger.info("Trying JavaScript to find and fill description field")
                driver.execute_script("""
                    var textareas = document.querySelectorAll('textarea');
                    for (var i = 0; i < textareas.length; i++) {
                        var textarea = textareas[i];
                        if (textarea.placeholder && textarea.placeholder.includes('candidate for this project')) {
                            textarea.value = arguments[0];
                            var event = new Event('input', { bubbles: true });
                            textarea.dispatchEvent(event);
                            return true;
                        }
                    }
                    return false;
                """, description_text)
                time.sleep(1)
                logger.info("Executed JavaScript to find and fill description")
                try:
                    textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    for textarea in textareas:
                        if textarea.get_attribute("value") and len(textarea.get_attribute("value")) > 10:
                            logger.info("Found textarea with text content")
                            description_field_found = True
                            break
                except:
                    pass
        if not description_field_found:
            logger.warning("Could not confirm description field was filled")
        else:
            logger.info("Description field successfully filled")
        # 7. Scroll to the end of the page before submitting
        logger.info("Scrolling to the end of the page before submitting")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        # 8. Submit bid
        try:
            logger.info("Looking for Place Bid button")
            place_bid_found = False
            for i in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
            place_bid_xpaths = [
                "//fl-button[@fltrackinglabel='PlaceBidButton']//button[contains(normalize-space(.), 'Place Bid')]",
                "//div[contains(@class,'BidFormBtn')]//button[contains(normalize-space(.), 'Place Bid')]",
                "//button[contains(@class,'ButtonElement') and contains(normalize-space(.), 'Place Bid')]"
            ]
            for xpath in place_bid_xpaths:
                try:
                    submit_btn = WebDriverWait(driver, 7).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(0.5)
                    submit_btn.click()
                    logger.info(f"Clicked Place Bid button using selector: {xpath}")
                    place_bid_found = True
                    break
                except Exception as e:
                    logger.info(f"Selector failed ({xpath}): {e}")
            if place_bid_found:
                logger.info("Bid placed successfully")
                return True, "Applied successfully!"
            else:
                logger.warning("Could not find Place Bid button by any method")
                return False, "Could not find Place Bid button"
        except Exception as e:
            logger.error(f"Failed to submit bid: {str(e)}")
            return False, f"Failed to submit bid: {str(e)}"
    except Exception as e:
        logger.error(f"General exception: {str(e)}")
        return False, str(e)
    finally:
        time.sleep(1)
        driver.quit()
        logger.info("Driver closed")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Freelancer auto-applier on a specific job link.")
    parser.add_argument("--job_link", type=str, default="https://www.freelancer.com/projects/azure/System-Engineer-Needed/details", help="Freelancer job link")
    parser.add_argument("--email", type=str, required=True, help="Freelancer email")
    parser.add_argument("--password", type=str, required=True, help="Freelancer password")
    args = parser.parse_args()
    labels = {"salary_expectations": "100", "availability": "7"}
    result, msg = apply_to_freelancer_job(args.job_link, None, labels, args.email, args.password, debug_mode=False)
    print(f"Result: {result}, Message: {msg}") 

    