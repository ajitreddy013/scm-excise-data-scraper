import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Helper Functions ---
def get_real_dropdown_options(driver, textbox_id):
    """Get all available options from an AJAX dropdown, filtering out placeholders"""
    try:
        textbox = driver.find_element(By.ID, textbox_id)
        textbox.click()
        time.sleep(1)
        options = set()
        selectors = [
            "ul li", "div[role='option']", ".dropdown-item", "option", "li", "div"
        ]
        placeholder_texts = [
            "select", "select...", "choose", "choose...", "please select", "select an option", "select option",
            "type :", "brand :", "brand details", "<< back", "select type", "select brand", "select category"
        ]
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 1:
                        if not any(placeholder in text.lower() for placeholder in placeholder_texts):
                            options.add(text)
                if options:
                    break
            except:
                continue
        if not options:
            textbox.send_keys("a")
            time.sleep(1)
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 1:
                            if not any(placeholder in text.lower() for placeholder in placeholder_texts):
                                options.add(text)
                    if options:
                        break
                except:
                    continue
        return list(options)
    except Exception as e:
        print(f"Error getting dropdown options: {e}")
        return []

def extract_clean_table_data(driver):
    try:
        table = driver.find_element(By.ID, "GridItems")
        rows = table.find_elements(By.TAG_NAME, "tr")
        clean_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                srno = cells[0].text.strip()
                itemname = cells[1].text.strip()
                size = cells[2].text.strip()
                bottles = cells[3].text.strip()
                # Skip empty rows
                if not srno or not itemname or not size or not bottles:
                    continue
                # Only keep rows where SrNo is a digit and size contains 'L' (for ML/CL/L)
                if srno.isdigit() and any(x in size.upper() for x in ["ML", "CL", "L"]):
                    clean_data.append({
                        'SrNo': srno,
                        'ItemName': itemname,
                        'Size': size,
                        'BottlesPerCase': bottles
                    })
        return clean_data
    except Exception as e:
        print(f"Error extracting clean table data: {e}")
        return []

def main():
    print("🔄 Systematic SCM Excise Scraper - Correct Navigation")
    print("=" * 70)
    URL = "https://scmexcise.mahaonline.gov.in/Retailer/"
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    all_clean_data = []
    try:
        print(f"🌐 Opening website: {URL}")
        driver.get(URL)
        time.sleep(3)
        print("\n🔐 Please login manually...")
        input("Press Enter after logging in...")
        print("\n📋 Clicking 'Masters' and 'Brand Details' on main page...")
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Masters"))).click()
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Brand Details"))).click()
        # Now switch to Frame0 for scraping
        wait.until(EC.presence_of_element_located((By.ID, "Frame0")))
        iframe = driver.find_element(By.ID, "Frame0")
        driver.switch_to.frame(iframe)
        wait.until(EC.presence_of_element_located((By.ID, "DDMainType_TextBox")))
        type_options = get_real_dropdown_options(driver, "DDMainType_TextBox")
        if not type_options:
            type_options = ["Fermented Beer", "Mild Beer", "Spirits", "Wines"]
        for type_index, type_option in enumerate(type_options):
            try:
                type_textbox = driver.find_element(By.ID, "DDMainType_TextBox")
                type_textbox.clear()
                type_textbox.send_keys(type_option)
                wait.until(lambda d: d.find_element(By.ID, "DDBrandName_TextBox").is_enabled())
                time.sleep(1)
                brand_options = get_real_dropdown_options(driver, "DDBrandName_TextBox")
                if not brand_options:
                    continue
                for brand_index, brand_option in enumerate(brand_options):
                    try:
                        brand_textbox = driver.find_element(By.ID, "DDBrandName_TextBox")
                        brand_textbox.clear()
                        brand_textbox.send_keys(brand_option)
                        show_button = driver.find_element(By.ID, "btnShow")
                        show_button.click()
                        wait.until(lambda d: d.find_element(By.ID, "GridItems"), message="Waiting for GridItems table...")
                        clean_data = extract_clean_table_data(driver)
                        for product in clean_data:
                            product_with_metadata = {
                                'Type': type_option,
                                'Brand': brand_option,
                                'SrNo': product['SrNo'],
                                'ItemName': product['ItemName'],
                                'Size': product['Size'],
                                'BottlesPerCase': product['BottlesPerCase']
                            }
                            all_clean_data.append(product_with_metadata)
                    except Exception as e:
                        print(f"    ❌ Error processing Brand {brand_option}: {e}")
                        continue
            except Exception as e:
                print(f"❌ Error processing Type {type_option}: {e}")
                continue
        # Deduplicate
        seen = set()
        deduped_data = []
        for row in all_clean_data:
            key = (row['Type'], row['Brand'], row['ItemName'], row['Size'], row['BottlesPerCase'])
            if key not in seen:
                seen.add(key)
                deduped_data.append(row)
        # Save full CSV
        filename = "systematic_brand_details.csv"
        with open(filename, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Type', 'Brand', 'SrNo', 'ItemName', 'Size', 'BottlesPerCase'])
            writer.writeheader()
            writer.writerows(deduped_data)
        print(f"✅ Clean data successfully saved to {filename}")
        # Save Brand/Size only CSV
        brand_size_seen = set()
        brand_size_rows = []
        for row in deduped_data:
            key = (row['Brand'], row['Size'])
            if key not in brand_size_seen:
                brand_size_seen.add(key)
                brand_size_rows.append({'Brand': row['Brand'], 'Size': row['Size']})
        with open("clean_brand_size.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Brand', 'Size'])
            writer.writeheader()
            writer.writerows(brand_size_rows)
        print(f"✅ Brand/Size data saved to clean_brand_size.csv")
        driver.switch_to.default_content()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        print("\n⏸️  Keeping browser open for inspection...")
        print("Press Enter to close...")
        input()
        driver.quit()
        print("👋 Browser closed. Goodbye!")

if __name__ == "__main__":
    main() 