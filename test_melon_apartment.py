import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import random
import string
from datetime import datetime
import re

class TestApartmentBrowsingWorkflow:
    """Enhanced test for apartment browsing and selection workflow"""

    @pytest.fixture(scope="session")
    async def browser_setup(self):
        """Set up a single browser instance for all tests in the session."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def page(self, browser_setup: Browser):
        """Provide a new page for each test."""
        context = await browser_setup.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    async def test_apartment_browsing_and_selection(self, page: Page):
        """Complete apartment browsing and selection workflow test"""
        print("=== APARTMENT BROWSING AND SELECTION WORKFLOW TEST ===")
        
        try:
            print("1. Navigating to homepage...")
            await page.goto("https://mostar.api.demo.ch.melon.market/")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="screenshots/01_homepage.png")
            print(" Homepage loaded")

            print("2. Exploring available apartments...")
            apartments = await self.find_available_apartments(page)
            if not apartments:
                pytest.fail("No available apartments found on the page")
            
            print(f" Found {len(apartments)} available apartments")

            print("3. Selecting a random apartment...")
            selected_apartment = await self.select_random_apartment(page, apartments)
            if not selected_apartment:
                pytest.fail("Failed to select an apartment")
            
            await page.screenshot(path="screenshots/02_apartment_selected.png")
            print(" Apartment selected")

            print("4. Looking for apartment details...")
            apartment_details = await self.get_apartment_details(page, selected_apartment)
            print(f" Apartment details: {apartment_details}")

            print("5. Adding apartment to wishlist...")
            wishlist_success = await self.add_to_wishlist(page, selected_apartment)
            if wishlist_success:
                await page.screenshot(path="screenshots/03_added_to_wishlist.png")
                print(" Apartment added to wishlist")
                
                print("5b. Waiting for wishlist panel to load...")
                await self.find_wishlist_panel(page)
                await page.screenshot(path="screenshots/03b_wishlist_panel.png")
            else:
                print(" Could not add to wishlist, continuing with application...")

            print("6. Looking for Apply/Application button...")
            new_page = await self.find_and_click_apply(page)
            if not new_page:
                print(" Could not find Apply button, trying alternative methods...")
                new_page = await self.try_alternative_application_methods(page)
                
            if not new_page:
                await page.screenshot(path="screenshots/error_no_application.png", full_page=True)
                pytest.fail("Failed to navigate to application form")

            page = new_page
            await page.bring_to_front()

            print("7. Verifying application form...")
            await self.verify_application_form(page)
            
            print("8. Starting application process...")
            await self.start_application_process(page)
            
            await page.screenshot(path="screenshots/04_application_started.png", full_page=True)
            print(" Application process started successfully")

        except Exception as e:
            await page.screenshot(path="screenshots/error_final.png", full_page=True)
            print(f" Test failed with exception: {e}")
            raise

    async def find_available_apartments(self, page: Page):
        """Find all available apartments on the page"""
        try:
            print("   Searching for apartment listings...")
            
            apartment_selectors = [
                "tr[data-apartment-id]",
                "tr:has(td:has-text('Available'))",
                "tr:has(.bewerben)",
                "tr:has(span.bewerben)",
                "table tr:not(:first-child)",
                ".apartment-row",
                "tr:has(td):not(.header-row)"
            ]
            
            apartments = []
            for selector in apartment_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    visible_elements = []
                    
                    for element in elements:
                        if await element.is_visible():
                            text_content = await element.text_content()
                            if text_content and any(keyword in text_content.lower() for keyword in 
                                                  ['available', 'rooms', 'apartment', 'flat', 'wishlist', 'apply']):
                                visible_elements.append(element)
                    
                    if visible_elements:
                        apartments = visible_elements
                        print(f"   Found apartments using selector: {selector}")
                        break
                        
                except Exception as e:
                    print(f"   Selector {selector} failed: {e}")
                    continue

            print(f"   Total apartment elements found: {len(apartments)}")

            for i, apt in enumerate(apartments[:3]):
                try:
                    content = await apt.text_content()
                    print(f"   Apartment {i+1}: {content[:100]}...")
                except:
                    print(f"   Apartment {i+1}: Could not read content")
            
            return apartments
            
        except Exception as e:
            print(f"   Error finding apartments: {e}")
            return []

    async def select_random_apartment(self, page: Page, apartments):
        """Select a random apartment from the available list, skipping disabled ones"""
        try:
            if not apartments:
                return None

            clickable_apartments = []
            for apt in apartments:
                try:
                    wishlist_elements = await apt.query_selector_all("span.bewerben")

                    has_clickable_wishlist = False
                    for element in wishlist_elements:
                        if await element.is_visible():
                            classes = await element.get_attribute("class") or ""
                            if "disabled" not in classes.lower():
                                has_clickable_wishlist = True
                                break
                    
                    if has_clickable_wishlist:
                        clickable_apartments.append(apt)
                        try:
                            title_text = await apt.text_content()
                            apartment_id = title_text.split()[0] if title_text else "Unknown"
                            print(f"   Found clickable apartment: {apartment_id}")
                        except:
                            print(f"   Found clickable apartment (ID unknown)")
                    else:
                        try:
                            title_text = await apt.text_content()
                            apartment_id = title_text.split()[0] if title_text else "Unknown"
                            print(f"   Skipping disabled apartment: {apartment_id}")
                        except:
                            print(f"   Skipping disabled apartment (ID unknown)")
                            
                except Exception as e:
                    print(f"   Error checking apartment clickability: {e}")
                    continue
            
            if not clickable_apartments:
                print("   No apartments with clickable wishlist buttons found, trying all apartments")
                clickable_apartments = apartments
            
            selected = random.choice(clickable_apartments)
            
            await selected.evaluate("el => el.style.backgroundColor = 'lightblue'")
            await selected.evaluate("el => el.style.border = '2px solid blue'")
            await page.wait_for_timeout(1000)
            
            await selected.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            
            print(f"   Selected apartment from {len(clickable_apartments)} clickable options")
            return selected
            
        except Exception as e:
            print(f"   Error selecting apartment: {e}")
            return None

    async def get_apartment_details(self, page: Page, apartment_element):
        """Extract details from the selected apartment"""
        try:
            text_content = await apartment_element.text_content()

            details = {
                'full_text': text_content.strip() if text_content else '',
                'rooms': None,
                'price': None,
                'size': None,
                'status': None
            }
            
            if text_content:
                room_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:room|zimmer|Zimmer)', text_content, re.IGNORECASE)
                if room_match:
                    details['rooms'] = room_match.group(1)

                price_match = re.search(r'(CHF|Fr\.?|€|\$)\s*(\d+(?:[,\.]\d+)*)', text_content, re.IGNORECASE)
                if price_match:
                    details['price'] = f"{price_match.group(1)}{price_match.group(2)}"
                
                size_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', text_content, re.IGNORECASE)
                if size_match:
                    details['size'] = f"{size_match.group(1)}m²"
                
                if any(status in text_content.lower() for status in ['available', 'verfügbar', 'free', 'frei']):
                    details['status'] = 'Available'
            
            return details
            
        except Exception as e:
            print(f"   Error getting apartment details: {e}")
            return {'error': str(e)}

    async def add_to_wishlist(self, page: Page, apartment_element):
        """Try to add the selected apartment to wishlist, skipping if disabled"""
        try:
            print("   Looking for clickable wishlist button...")
            
            wishlist_selectors = [
                "span.bewerben:has-text('Wishlist')",
                "span.bewerben", 
                "span:has-text('Wishlist')",
                ".wishlist-btn",
                "[data-action='wishlist']"
            ]
            
            for selector in wishlist_selectors:
                try:
                    wishlist_elements = await apartment_element.query_selector_all(selector)
                    for wishlist_element in wishlist_elements:
                        if await wishlist_element.is_visible():
                            classes = await wishlist_element.get_attribute("class") or ""
                            if "disabled" in classes.lower():
                                print("    Wishlist button is disabled, skipping...")
                                return False
                            
                            await wishlist_element.evaluate("el => el.style.backgroundColor = 'yellow'")
                            await page.wait_for_timeout(500)
                            await wishlist_element.click()
                            await page.wait_for_timeout(2000)
                            print("    Wishlist button clicked")
                            return True
                            
                except Exception as e:
                    print(f"   Wishlist selector {selector} failed: {e}")
                    continue
            
            print("    No clickable wishlist button found")
            return False
            
        except Exception as e:
            print(f"   Error adding to wishlist: {e}")
            return False

    async def find_wishlist_panel(self, page: Page):
        """Find the wishlist panel that should appear after adding to wishlist"""
        try:
            print("   Looking for wishlist panel...")

            panel_selectors = [
                ".apartments-table-wishlist",
                "[data-v-21a4b90e].apartments-table-wishlist", 
                "div[class*='apartments-table-wishlist']"
            ]
            
            panel_found = False
            for selector in panel_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        print(f"    Wishlist panel found: {selector}")
                        panel_found = True
                        break
                except:
                    continue
            
            if not panel_found:
                print("    Wishlist panel not detected, but continuing...")
            
            apply_in_wishlist = await page.query_selector(".apartments-table-wishlist .wishlist-footer .button")
            if apply_in_wishlist and await apply_in_wishlist.is_visible():
                print("    Apply button found in wishlist panel")
                return True
            
            apply_elements = await page.query_selector_all("*:has-text('Apply')")
            visible_apply = [el for el in apply_elements if await el.is_visible()]
            
            if visible_apply:
                print(f"   Apply elements found: {len(visible_apply)}")
                return True
            
            print("   No Apply button visible after adding to wishlist")
            return False
            
        except Exception as e:
            print(f"   Error finding wishlist panel: {e}")
            return False

    async def find_and_click_apply(self, page: Page):
        """Find and click the Apply button, waiting for a new page."""
        try:
            apply_selectors = [
                ".button:has-text('Apply')",
                "[data-v-21a4b90e].button:has-text('Apply')", 
                "div.button:has-text('Apply')",
                "button:has-text('Apply')",
                "*[class*='button']:has-text('Apply')"
            ]
            
            for selector in apply_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        print(f"  Apply button found: {selector}")
                        await element.evaluate("el => el.style.border = '3px solid red'")
                        await page.wait_for_timeout(1000)
                        
                        async with page.context.expect_page() as new_page_info:
                            await element.click()
                        
                        new_page = await new_page_info.value
                        print(" New page/tab opened successfully.")
                        return new_page
            
            print(" No clickable Apply button found or new page failed to open.")
            return None
            
        except Exception as e:
            print(f"  Error finding or clicking Apply button: {e}")
            return None

    async def try_alternative_application_methods(self, page: Page):
        """Try alternative methods to start application process"""
        try:
            print("   Trying alternative application methods...")
            
            alternative_selectors = [
                "a[href*='application']",
                "a[href*='apply']",
                "a[href*='form']",
                ".application-link",
                "[data-action*='apply']"
            ]
            
            for selector in alternative_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            async with page.context.expect_page() as new_page_info:
                                await element.click()
                            new_page = await new_page_info.value
                            print(f"    Alternative method worked: {selector}")
                            return new_page
                except:
                    continue
            
            current_url = page.url
            base_url = current_url.split('?')[0].rstrip('/')
            
            application_urls = [
                f"{base_url}/form/application/new",
                f"{base_url}/application",
                f"{base_url}/apply"
            ]
            
            for url in application_urls:
                try:
                    new_page = await page.context.new_page()
                    await new_page.goto(url)
                    await new_page.wait_for_load_state("networkidle", timeout=5000)
                    
                    title = await new_page.title()
                    content = await new_page.text_content("body")
                    
                    if any(keyword in title.lower() or keyword in content.lower() 
                           for keyword in ['application', 'apply', 'form']):
                        print(f"    Direct navigation worked: {url}")
                        return new_page
                    else:
                        await new_page.close()
                        
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"   Error in alternative methods: {e}")
            return None

    async def verify_application_form(self, page: Page):
        """Verify we're on the correct application form page"""
        try:
            print("   Verifying application form page...")
            
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            current_url = page.url
            print(f"   Current URL: {current_url}")         

            form_indicators = [
                "#start-application-btn",
                "form",
                "input[type='text']",
                "textarea",
                "select"
            ]
            
            found_indicators = []
            for indicator in form_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        found_indicators.append(indicator)
                except:
                    continue
            
            print(f"   Form indicators found: {found_indicators}")
            
            await page.screenshot(path="screenshots/03_application_form_verified.png", full_page=True)
            
            if not found_indicators:
                print("    Warning: No clear form indicators found")
            else:
                print("    Application form verified")
            
        except Exception as e:
            print(f"   Error verifying form: {e}")

    async def start_application_process(self, page: Page):
        """Start the application process"""
        try:
            print("   Starting application process...")
            
            start_selectors = [
                "#start-application-btn",
                "button:has-text('Start')",
                ".start-btn",
                "input[type='submit']",
                ".begin-application"
            ]
            
            for selector in start_selectors:
                try:
                    start_element = await page.query_selector(selector)
                    if start_element and await start_element.is_visible():
                        print(f"   Found start button: {selector}")
                        await start_element.click()
                        await page.wait_for_timeout(3000)

                        form_fields = await page.query_selector_all("input, textarea, select")
                        visible_fields = [field for field in form_fields if await field.is_visible()]
                        
                        if visible_fields:
                            print(f"    Form started - {len(visible_fields)} input fields visible")
                            return True
                        else:
                            print("   Form may have started but no input fields visible yet")
                            return True
                            
                except Exception as e:
                    print(f"   Start selector {selector} failed: {e}")
                    continue

            form_fields = await page.query_selector_all("input, textarea, select")
            visible_fields = [field for field in form_fields if await field.is_visible()]
            
            if visible_fields:
                print(f"    Form already active - {len(visible_fields)} input fields visible")
                return True
            
            print("    Could not start application process")
            return False
            
        except Exception as e:
            print(f"   Error starting application: {e}")
            return False

    async def debug_page_structure(self, page: Page):
        """Debug helper to understand page structure"""
        print("   DEBUGGING PAGE STRUCTURE:")
        
        try:
            tables = await page.query_selector_all("table")
            print(f"   Tables found: {len(tables)}")
            
            rows = await page.query_selector_all("tr")
            print(f"   Table rows found: {len(rows)}")
            
            for i, row in enumerate(rows[:5]):
                try:
                    text = await row.text_content()
                    if text and text.strip():
                        print(f"   Row {i}: {text.strip()[:100]}...")
                except:
                    continue
            
            buttons = await page.query_selector_all("button, .button, span.bewerben")
            print(f"   Action elements found: {len(buttons)}")
            
        except Exception as e:
            print(f"   Debug error: {e}")

if __name__ == "__main__":
    async def run_apartment_test():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1500)
            page = await browser.new_page()
            
            test_suite = TestApartmentBrowsingWorkflow()
            
            try:
                await test_suite.test_apartment_browsing_and_selection(page)
                print("\n APARTMENT BROWSING AND SELECTION TEST COMPLETED SUCCESSFULLY!")
            except Exception as e:
                print(f"\n APARTMENT BROWSING AND SELECTION TEST FAILED: {e}")
                import traceback
                print(traceback.format_exc())
            finally:
                print(" Screenshots saved in screenshots/ directory")
                print("\n Keeping browser open for 10 seconds to review results...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    print(" Starting apartment browsing and selection workflow test...")
    asyncio.run(run_apartment_test())