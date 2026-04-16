"""
FlexJobs Job Scraper
====================
Requirements:
    pip install selenium webdriver-manager

Usage:
    1. Apna EMAIL aur PASSWORD neeche fill karo
    2. SEARCH_URL mein apni search paste karo
    3. Run: python flexjobs_scraper.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# ============================================================
#  YAHAN APNI DETAILS BHARO
# ============================================================
EMAIL    = "your_email@example.com"       # <-- apna email
PASSWORD = "your_password_here"           # <-- apna password

# Jis URL se scrape karna hai (koi bhi FlexJobs search URL paste karo)
SEARCH_URL = "https://www.flexjobs.com/search?searchkeyword=Video%20Editor&usecLocation=true&fromHeader=true"

OUTPUT_FILE = "flexjobs_companies.txt"    # result is file mein jayega
# ============================================================

def init_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # browser dikhana nahi? to uncomment karo
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login(driver):
    print("[*] Login page khul raha hai...")
    driver.get("https://www.flexjobs.com/login")
    wait = WebDriverWait(driver, 15)

    # Email
    email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
    email_field.clear()
    email_field.send_keys(EMAIL)

    # Password
    pass_field = driver.find_element(By.ID, "password")
    pass_field.clear()
    pass_field.send_keys(PASSWORD)

    # Submit
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("[*] Login ho raha hai, wait karo...")
    time.sleep(4)


def scrape_all_pages(driver):
    driver.get(SEARCH_URL)
    time.sleep(3)

    all_companies = []
    page_num = 1

    while True:
        print(f"\n[*] Page {page_num} scrape ho raha hai...")

        # Companies collect karo current page se
        companies = scrape_page(driver)
        all_companies.extend(companies)
        print(f"    {len(companies)} companies mili is page pe")

        # Next page button dhundo
        try:
            next_btn = driver.find_element(
                By.CSS_SELECTOR, "a[aria-label='Next page'], a.next, li.next a"
            )
            if next_btn and next_btn.is_enabled():
                next_btn.click()
                time.sleep(3)
                page_num += 1
            else:
                print("[*] Koi aur page nahi mila.")
                break
        except Exception:
            print("[*] Next page button nahi mila — scraping complete!")
            break

    return all_companies


def scrape_page(driver):
    companies = []

    # FlexJobs company selectors (multiple try karta hai)
    selectors = [
        "h3.company",
        "span.company",
        "div.job-item h3.company",
        "a.company-name",
        "[class*='company']",
        "h2.job-title + span",   # fallback
    ]

    for sel in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        if elements:
            for el in elements:
                name = el.text.strip()
                if name and name not in companies:
                    companies.append(name)
            break  # kaam kar gaya, aage mat jao

    # Agar kuch na mila toh broad search
    if not companies:
        # Job cards dhundo aur unse company nikalo
        cards = driver.find_elements(By.CSS_SELECTOR, "li.job-item, div.job-item, article")
        for card in cards:
            try:
                spans = card.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    txt = span.text.strip()
                    # Company names usually short aur Title Case hoti hain
                    if txt and len(txt) < 60 and txt.istitle():
                        if txt not in companies:
                            companies.append(txt)
                            break
            except Exception:
                continue

    return companies


def save_to_file(companies):
    unique = sorted(set(companies))
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"FlexJobs - Scraped Companies ({len(unique)} total)\n")
        f.write("=" * 50 + "\n\n")
        for i, company in enumerate(unique, 1):
            f.write(f"{i}. {company}\n")
    print(f"\n[✓] {len(unique)} unique companies '{OUTPUT_FILE}' mein save ho gayi!")


def main():
    driver = init_driver()
    try:
        login(driver)

        # Check karo login hua ya nahi
        if "login" in driver.current_url.lower():
            print("[!] Login fail laga — check karo email/password")
            input("    Manually login karo browser mein, phir Enter dabaao...")

        print("[*] Search page pe ja raha hoon...")
        companies = scrape_all_pages(driver)

        if companies:
            save_to_file(companies)
        else:
            print("[!] Koi company nahi mili. Selectors update karne par sochein.")
            # Debug: page source save karo
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("    debug_page.html mein page source save kiya — inspect karo.")

    finally:
        input("\nEnter dabaao browser band karne ke liye...")
        driver.quit()


if __name__ == "__main__":
    main()