import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_real_dropdown_options(driver, textbox_id):
    """Get all available options from an AJAX dropdown, filtering out placeholders"""
    try:
        # Click on the textbox to open dropdown
        textbox = driver.find_element(By.ID, textbox_id)
        textbox.click()
        time.sleep(2)
        
        # Look for dropdown options
        options = []
        
        # Try different selectors for dropdown options
        selectors = [
            "ul li",  # List items
            "div[role='option']",  # Divs with role option
            ".dropdown-item",  # Bootstrap dropdown items
            "option",  # Standard options
            "li",  # Any list items
            "div"  # Any divs
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and text not in options and len(text) > 1:
                        # Filter out placeholder texts
                        placeholder_texts = [
                            "select", "select...", "choose", "choose...", 
                            "please select", "select an option", "select option",
                            "type :", "brand :", "brand details", "<< back",
                            "select type", "select brand", "select category"
                        ]
                        
                        # Check if this is a real option (not a placeholder)
                        is_placeholder = False
                        for placeholder in placeholder_texts:
                            if placeholder.lower() in text.lower():
                                is_placeholder = True
                                break
                        
                        if not is_placeholder and len(text) > 2:
                            options.append(text)
                
                if options:
                    break
            except:
                continue
        
        # If no options found, try typing to trigger dropdown
        if not options:
            textbox.send_keys("a")  # Type something to trigger dropdown
            time.sleep(2)
            # Try the selectors again
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and text not in options and len(text) > 1:
                            # Filter out placeholder texts
                            placeholder_texts = [
                                "select", "select...", "choose", "choose...", 
                                "please select", "select an option", "select option",
                                "type :", "brand :", "brand details", "<< back",
                                "select type", "select brand", "select category"
                            ]
                            
                            is_placeholder = False
                            for placeholder in placeholder_texts:
                                if placeholder.lower() in text.lower():
                                    is_placeholder = True
                                    break
                            
                            if not is_placeholder and len(text) > 2:
                                options.append(text)
                    
                    if options:
                        break
                except:
                    continue
        
        return options
    except Exception as e:
        print(f"Error getting dropdown options: {e}")
        return []

def extract_clean_table_data(driver, table):
    """Extract clean, structured data from a table"""
    try:
        rows = table.find_elements(By.TAG_NAME, "tr")
        clean_data = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:  # Look for rows with enough columns for product data
                cell_texts = [cell.text.strip() for cell in cells]
                
                # Check if this looks like product data (has SrNo, ItemName, Size, Bottles)
                if (cell_texts[0].isdigit() and 
                    len(cell_texts) >= 4 and 
                    any('ML' in cell_texts[i] for i in range(2, min(4, len(cell_texts))))):
                    
                    clean_data.append({
                        'SrNo': cell_texts[0],
                        'ItemName': cell_texts[1] if len(cell_texts) > 1 else '',
                        'Size': cell_texts[2] if len(cell_texts) > 2 else '',
                        'BottlesPerCase': cell_texts[3] if len(cell_texts) > 3 else ''
                    })
        
        return clean_data
    except Exception as e:
        print(f"Error extracting clean table data: {e}")
        return []

def main():
    print("🔄 Systematic SCM Excise Scraper - All Types (Skip First Options)")
    print("=" * 70)
    
    # --- Configuration ---
    URL = "https://scmexcise.mahaonline.gov.in/Retailer/"
    
    # Setup browser
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    
    all_clean_data = []  # Store all clean extracted data
    
    try:
        # Navigate to the site
        print(f"🌐 Opening website: {URL}")
        driver.get(URL)
        time.sleep(3)
        
        print("\n🔐 Please login manually...")
        input("Press Enter after logging in...")
        
        # Navigate to Brand Details
        print("\n📋 Navigating to Brand Details...")
        driver.find_element(By.LINK_TEXT, "Masters").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "Brand Details").click()
        time.sleep(5)
        
        print("✅ Clicked Brand Details link")
        
        # Wait for iframe to load and switch to it
        print("\n🔄 Looking for iframe...")
        time.sleep(3)
        
        # Find and switch to iframe
        iframe = driver.find_element(By.ID, "Frame0")
        print("✅ Found iframe 'Frame0'")
        driver.switch_to.frame(iframe)
        print("✅ Switched to iframe")
        time.sleep(3)
        
        print(f"📄 iFrame page title: {driver.title}")
        print(f"🔗 iFrame URL: {driver.current_url}")
        
        # Get all available Types (skip first option)
        print("\n🔍 Getting all available Types...")
        type_options = get_real_dropdown_options(driver, "DDMainType_TextBox")
        print(f"✅ Found {len(type_options)} real Types: {type_options}")
        
        if not type_options:
            print("❌ No real Type options found. Trying manual approach...")
            # Try some common types
            type_options = ["Fermented Beer", "Mild Beer", "Spirits", "Wines"]
        
        # Process all types (skip first option if it's a placeholder)
        for type_index, type_option in enumerate(type_options):
            print(f"\n{'='*70}")
            print(f"📝 Processing Type {type_index + 1}/{len(type_options)}: {type_option}")
            print(f"{'='*70}")
            
            try:
                # Select Type
                type_textbox = driver.find_element(By.ID, "DDMainType_TextBox")
                type_textbox.clear()
                type_textbox.send_keys(type_option)
                time.sleep(2)
                print(f"✅ Selected Type: {type_option}")
                
                # Wait 2-3 seconds for brands to load
                print("⏳ Waiting 3 seconds for brands to load...")
                time.sleep(3)
                
                # Get available Brands for this Type (skip first option)
                print(f"🔍 Getting Brands for Type: {type_option}")
                brand_options = get_real_dropdown_options(driver, "DDBrandName_TextBox")
                print(f"✅ Found {len(brand_options)} real Brands for {type_option}")
                
                if not brand_options:
                    print(f"⚠️  No real Brand options found for {type_option}. Skipping...")
                    continue
                
                # Show first few brands
                if len(brand_options) > 5:
                    print(f"   Sample Brands: {brand_options[:5]}...")
                else:
                    print(f"   All Brands: {brand_options}")
                
                # For each Brand (skip first option), extract clean data
                for brand_index, brand_option in enumerate(brand_options):
                    print(f"  📝 Processing Brand {brand_index + 1}/{len(brand_options)}: {brand_option}")
                    
                    try:
                        # Select Brand
                        brand_textbox = driver.find_element(By.ID, "DDBrandName_TextBox")
                        brand_textbox.clear()
                        brand_textbox.send_keys(brand_option)
                        time.sleep(2)
                        print(f"    ✅ Selected Brand: {brand_option}")
                        
                        # Click Show button
                        show_button = driver.find_element(By.ID, "btnShow")
                        show_button.click()
                        print(f"    🔘 Clicked Show button")
                        time.sleep(5)  # Wait for data to load
                        
                        # Look for data table and extract clean data
                        tables = driver.find_elements(By.TAG_NAME, "table")
                        if tables:
                            # Use the first table that has data
                            for table in tables:
                                clean_data = extract_clean_table_data(driver, table)
                                if clean_data:
                                    print(f"    ✅ Found {len(clean_data)} clean product records")
                                    
                                    # Add metadata to each product record
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
                                    break
                            else:
                                print(f"    ⚠️  No clean data found for {type_option} - {brand_option}")
                        else:
                            print(f"    ⚠️  No table found for {type_option} - {brand_option}")
                        
                    except Exception as e:
                        print(f"    ❌ Error processing Brand {brand_option}: {e}")
                        continue
                
                print(f"\n✅ Completed processing {type_option}")
                print(f"📊 Total records so far: {len(all_clean_data)}")
                
            except Exception as e:
                print(f"❌ Error processing Type {type_option}: {e}")
                continue
        
        # Save all collected clean data
        print(f"\n{'='*70}")
        print(f"💾 Saving all collected clean data...")
        print(f"📊 Total clean product records collected: {len(all_clean_data)}")
        print(f"{'='*70}")
        
        if all_clean_data:
            filename = "systematic_brand_details.csv"
            with open(filename, "w", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Type', 'Brand', 'SrNo', 'ItemName', 'Size', 'BottlesPerCase'])
                writer.writeheader()
                writer.writerows(all_clean_data)
            
            print(f"✅ Clean data successfully saved to {filename}")
            print(f"📁 File contains {len(all_clean_data)} product records")
            
            # Show summary by type
            type_summary = {}
            for record in all_clean_data:
                type_name = record['Type']
                if type_name not in type_summary:
                    type_summary[type_name] = {'brands': set(), 'products': 0}
                type_summary[type_name]['brands'].add(record['Brand'])
                type_summary[type_name]['products'] += 1
            
            print(f"\n📋 Summary by Type:")
            for type_name, stats in type_summary.items():
                print(f"  {type_name}: {len(stats['brands'])} brands, {stats['products']} products")
            
            # Show sample data
            print(f"\n📋 Sample clean data (first 5 records):")
            for i, record in enumerate(all_clean_data[:5]):
                print(f"  Record {i+1}: {record['Type']} | {record['Brand']} | {record['ItemName']} | {record['Size']} | {record['BottlesPerCase']} bottles/case")
        else:
            print("❌ No clean data was collected")
        
        # Switch back to main frame
        driver.switch_to.default_content()
        print("✅ Switched back to main frame")
        
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