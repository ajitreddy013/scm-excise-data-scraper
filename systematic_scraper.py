import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
import os

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

def print_all_links(driver):
    print("\n--- All clickable links on main page ---")
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links:
        text = link.text.strip()
        href = link.get_attribute('href')
        if text:
            print(f"  Link: '{text}' | href: {href}")
    return [link.text.strip() for link in links if link.text.strip()]

def click_link_by_text(driver, wait, text, partial=False):
    try:
        if not partial:
            elem = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, text)))
        else:
            elem = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, text)))
        elem.click()
        print(f"✅ Clicked link: '{text}' (partial={partial})")
        return True
    except Exception as e:
        print(f"❌ Could not click link: '{text}' (partial={partial}) - {e}")
        return False

def print_iframe_elements(driver):
    print("\n--- Diagnosing iframes and elements after clicking 'Brand Details' ---")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Found {len(iframes)} iframes:")
    for idx, iframe in enumerate(iframes):
        iframe_id = iframe.get_attribute('id')
        iframe_name = iframe.get_attribute('name')
        print(f"  [{idx}] id: {iframe_id}, name: {iframe_name}")
    for idx, iframe in enumerate(iframes):
        iframe_id = iframe.get_attribute('id')
        iframe_name = iframe.get_attribute('name')
        print(f"\n--- Iframe [{idx}] id: {iframe_id}, name: {iframe_name} ---")
        driver.switch_to.default_content()
        driver.switch_to.frame(iframe)
        # Print all select elements with IDs
        selects = driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            sel_id = sel.get_attribute('id')
            print(f"  Select: id={sel_id}")
        # Print all input elements with IDs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            inp_id = inp.get_attribute('id')
            inp_type = inp.get_attribute('type')
            print(f"  Input: id={inp_id}, type={inp_type}")
        # Print all tables with IDs
        tables = driver.find_elements(By.TAG_NAME, "table")
        for tab in tables:
            tab_id = tab.get_attribute('id')
            print(f"  Table: id={tab_id}")
        driver.switch_to.default_content()

def find_first_two_dropdowns(driver):
    # Try to find the first two <select> or <input> elements that look like dropdowns
    selects = driver.find_elements(By.TAG_NAME, "select")
    if len(selects) >= 2:
        return selects[0], selects[1]
    # If not enough <select>, try <input> with type=text or type=search
    inputs = [el for el in driver.find_elements(By.TAG_NAME, "input") if el.get_attribute('type') in (None, '', 'text', 'search')]
    if len(inputs) >= 2:
        return inputs[0], inputs[1]
    # Fallback: return None
    return None, None

def get_dropdown_options_generic(dropdown):
    # For <select> elements
    if dropdown.tag_name == 'select':
        options = dropdown.find_elements(By.TAG_NAME, 'option')
        return [opt.text.strip() for opt in options if opt.text.strip()]
    # For <input> elements, try to click and get visible list items
    dropdown.click()
    time.sleep(1)
    items = dropdown.find_elements(By.XPATH, "../../..//li")
    return [item.text.strip() for item in items if item.text.strip()]

def print_all_elements_in_frame(driver):
    print("\n--- All elements in Frame0 ---")
    elements = driver.find_elements(By.XPATH, '//*')
    for el in elements:
        tag = el.tag_name
        el_id = el.get_attribute('id')
        el_name = el.get_attribute('name')
        el_type = el.get_attribute('type')
        el_class = el.get_attribute('class')
        text = el.text.strip()
        if el_id or el_name or el_type or el_class or text:
            print(f"  <{tag}> id={el_id} name={el_name} type={el_type} class={el_class} text='{text[:40]}'")

def get_combobox_options(driver, textbox_id, option_list_id, wait):
    textbox = driver.find_element(By.ID, textbox_id)
    textbox.click()
    # Wait for the option list to be visible
    wait.until(lambda d: d.find_element(By.ID, option_list_id).is_displayed())
    option_list = driver.find_element(By.ID, option_list_id)
    items = option_list.find_elements(By.TAG_NAME, 'li')
    return [item.text.strip() for item in items if item.text.strip() and 'select' not in item.text.lower()]

def select_combobox_option(driver, textbox_id, option_list_id, value, wait):
    textbox = driver.find_element(By.ID, textbox_id)
    textbox.clear()
    textbox.send_keys(value)
    time.sleep(0.5)
    textbox.click()
    wait.until(lambda d: d.find_element(By.ID, option_list_id).is_displayed())
    option_list = driver.find_element(By.ID, option_list_id)
    items = option_list.find_elements(By.TAG_NAME, 'li')
    for item in items:
        if item.text.strip() == value:
            driver.execute_script("arguments[0].scrollIntoView();", item)
            item.click()
            time.sleep(0.5)
            return True
    return False

def save_screenshot(driver, label):
    filename = f"screenshot_{label}.png"
    driver.save_screenshot(filename)
    print(f"📸 Screenshot saved: {filename}")

def main():
    print("🔄 Systematic SCM Excise Scraper - AJAX ComboBox Debug Screenshot")
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
        link_texts = print_all_links(driver)
        print("\n📋 Trying to click 'Masters' on main page...")
        found = click_link_by_text(driver, wait, "Masters")
        if not found:
            found = click_link_by_text(driver, wait, "Masters", partial=True)
        if not found:
            print("❌ 'Masters' link not found. Available links:")
            for t in link_texts:
                print(f"  '{t}'")
            return
        print("\n📋 Trying to click 'Brand Details' on main page...")
        link_texts = print_all_links(driver)
        found = click_link_by_text(driver, wait, "Brand Details")
        if not found:
            found = click_link_by_text(driver, wait, "Brand Details", partial=True)
        if not found:
            print("❌ 'Brand Details' link not found. Available links:")
            for t in link_texts:
                print(f"  '{t}'")
            return
        # Switch to Frame0 for scraping
        print("Switching to Frame0...")
        wait.until(EC.presence_of_element_located((By.ID, "Frame0")))
        iframe = driver.find_element(By.ID, "Frame0")
        driver.switch_to.frame(iframe)
        time.sleep(2)
        print("Saving screenshot after switching to Frame0...")
        save_screenshot(driver, "after_frame0")
        print("Looking for DDMainType_TextBox and DDBrandName_TextBox...")
        type_box = driver.find_elements(By.ID, "DDMainType_TextBox")
        brand_box = driver.find_elements(By.ID, "DDBrandName_TextBox")
        print(f"  Found {len(type_box)} elements with id=DDMainType_TextBox")
        print(f"  Found {len(brand_box)} elements with id=DDBrandName_TextBox")
        print("Looking for DDMainType_OptionList and DDBrandName_OptionList...")
        type_list = driver.find_elements(By.ID, "DDMainType_OptionList")
        brand_list = driver.find_elements(By.ID, "DDBrandName_OptionList")
        print(f"  Found {len(type_list)} elements with id=DDMainType_OptionList")
        print(f"  Found {len(brand_list)} elements with id=DDBrandName_OptionList")
        # Continue with the rest of the script as before...
        # (You can uncomment the rest of the scraping logic here after debugging)
        # Get all type options from ComboBox
        type_options = get_combobox_options(driver, "DDMainType_TextBox", "DDMainType_OptionList", wait)
        print(f"Found {len(type_options)} type options: {type_options}")
        for type_val in type_options:
            try:
                # Select type
                select_combobox_option(driver, "DDMainType_TextBox", "DDMainType_OptionList", type_val, wait)
                time.sleep(1)
                # Get all brand options for this type
                brand_options = get_combobox_options(driver, "DDBrandName_TextBox", "DDBrandName_OptionList", wait)
                print(f"  Type '{type_val}': {len(brand_options)} brands")
                for brand_val in brand_options:
                    try:
                        select_combobox_option(driver, "DDBrandName_TextBox", "DDBrandName_OptionList", brand_val, wait)
                        time.sleep(1)
                        # Click Show button
                        try:
                            show_button = driver.find_element(By.ID, "btnShow")
                            show_button.click()
                            time.sleep(2)
                        except:
                            pass
                        # Extract table data
                        clean_data = extract_clean_table_data(driver)
                        for product in clean_data:
                            product_with_metadata = {
                                'Type': type_val,
                                'Brand': brand_val,
                                'SrNo': product['SrNo'],
                                'ItemName': product['ItemName'],
                                'Size': product['Size'],
                                'BottlesPerCase': product['BottlesPerCase']
                            }
                            all_clean_data.append(product_with_metadata)
                    except Exception as e:
                        print(f"    ❌ Error processing Brand '{brand_val}': {e}")
                        continue
            except Exception as e:
                print(f"❌ Error processing Type '{type_val}': {e}")
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