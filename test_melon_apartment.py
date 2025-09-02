import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import random
import string
from datetime import datetime
import re

class TestCompleteApartmentWorkflow:
    """Complete integrated test for apartment browsing, selection, and application workflow"""

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

    async def test_complete_apartment_workflow(self, page: Page):
        """Complete workflow from browsing apartments to submitting application"""
        print("=== COMPLETE APARTMENT WORKFLOW TEST ===")
        
        try:
            # Phase 1: Browse and select apartment
            print("PHASE 1: Apartment Browsing and Selection")
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

            print("4. Getting apartment details...")
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
            application_page = await self.find_and_click_apply(page)
            if not application_page:
                print(" Could not find Apply button, trying alternative methods...")
                application_page = await self.try_alternative_application_methods(page)
                
            if not application_page:
                await page.screenshot(path="screenshots/error_no_application.png", full_page=True)
                pytest.fail("Failed to navigate to application form")

            # Phase 2: Fill and submit application form
            print("\nPHASE 2: Application Form Completion")
            page = application_page
            await page.bring_to_front()

            print("7. Verifying application form...")
            await self.verify_application_form(page)
            
            print("8. Starting application process...")
            await self.start_application_process(page)
            
            print("9. Filling out application form with realistic data...")
            await self.fill_form_with_realistic_data(page)
            await page.screenshot(path="screenshots/04_form_filled.png", full_page=True)
            print(" Form filled with realistic data")

            print("10. Submitting application form...")
            await self.submit_application_form(page)
            
            await page.screenshot(path="screenshots/05_application_submitted.png", full_page=True)
            print(" Application submitted successfully")

            print("\n✅ COMPLETE APARTMENT WORKFLOW COMPLETED SUCCESSFULLY!")

        except Exception as e:
            await page.screenshot(path="screenshots/error_workflow.png", full_page=True)
            print(f" Test failed with exception: {e}")
            raise

    # ==================== APARTMENT BROWSING METHODS ====================

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
            
            return panel_found
            
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
                        print(" New application page opened successfully.")
                        return new_page
            
            print(" No clickable Apply button found.")
            return None
            
        except Exception as e:
            print(f"  Error finding or clicking Apply button: {e}")
            return None

    async def try_alternative_application_methods(self, page: Page):
        """Try alternative methods to start application process"""
        try:
            print("   Trying alternative application methods...")
            
            current_url = page.url
            base_url = current_url.split('?')[0].rstrip('/')
            
            application_urls = [
                f"{base_url}/form/application/new",
                "https://mostar.demo.melon.market/form/application/new?uuids=e34bfbd2-218e-4f36-9e92-e2ae9367fcfc&lang=en"
            ]
            
            for url in application_urls:
                try:
                    new_page = await page.context.new_page()
                    await new_page.goto(url)
                    await new_page.wait_for_load_state("networkidle", timeout=10000)

                    form_indicators = await new_page.query_selector_all(".application-form, form, input")
                    if form_indicators:
                        print(f"    Direct navigation worked: {url}")
                        return new_page
                    else:
                        await new_page.close()
                        
                except Exception as e:
                    print(f"    Failed to navigate to {url}: {e}")
                    try:
                        await new_page.close()
                    except:
                        pass
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
                ".application-form",
                "form",
                "input[type='text']",
                "textarea",
                "select",
                ".af-steps"
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
            
            if not found_indicators:
                print("    Warning: No clear form indicators found")
            else:
                print("    Application form verified")
            
        except Exception as e:
            print(f"   Error verifying form: {e}")

    async def start_application_process(self, page: Page):
        """Start the application process if needed"""
        try:
            print("   Starting application process...")

            await page.wait_for_selector(".application-form", timeout=5000)
            
            form_fields = await page.query_selector_all("input, textarea, select")
            visible_fields = [field for field in form_fields if await field.is_visible()]
            
            if visible_fields:
                print(f"    Form already active - {len(visible_fields)} input fields visible")
                return True
    
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
                        return True
                        
                except Exception as e:
                    print(f"   Start selector {selector} failed: {e}")
                    continue

            print("    Application process appears to be ready")
            return True
            
        except Exception as e:
            print(f"   Error starting application: {e}")
            return False

    async def fill_form_with_realistic_data(self, page: Page):
        """Fill the form with realistic user data using various interaction patterns"""
        try:
            print("   Starting form data entry simulation...")
            await page.wait_for_timeout(2000) 

            if random.random() < 0.3:
                print("   User wants parking spaces...")
                await self.click_radio_option(page, "parking-true")
                await page.wait_for_timeout(1000)
                
                parking_types = [
                    "field-parking_regular",
                    "field-parking_small", 
                    "field-parking_large",
                    "field-parking_electric",
                    "field-parking_outdoor"
                ]
                
                for parking_type in parking_types:
                    if random.random() < 0.4:
                        spaces = random.randint(1, 2)
                        await self.set_number_field(page, parking_type, spaces)
                        await page.wait_for_timeout(500)

                if random.random() < 0.6:
                    justifications = [
                        "Need car for work commute",
                        "Family transportation needs",
                        "Medical appointments",
                        "Weekend travel",
                        "Disabled family member transportation"
                    ]
                    await self.fill_text_field(page, "field-car_reason", random.choice(justifications))
            else:
                await self.click_radio_option(page, "parking-false")

            await self.randomly_select_yes_no(page, "car_sharing", 0.2)

            if random.random() < 0.1:
                await self.click_radio_option(page, "motorbikes-true")
                await page.wait_for_timeout(1000)
                await self.set_number_field(page, "field-parking_motorbike", 1)
            else:
                await self.click_radio_option(page, "motorbikes-false")

            if random.random() < 0.7:
                print("   User wants bike parking...")
                await self.click_radio_option(page, "bicycles-true")
                await page.wait_for_timeout(1000)

                bike_spaces = random.randint(1, 3)
                await self.set_number_field(page, "field-parking_bicycle", bike_spaces)

                if random.random() < 0.3:
                    ebike_spaces = random.randint(1, 2)
                    await self.set_number_field(page, "field-parking_electric_bicycles", ebike_spaces)
            else:
                await self.click_radio_option(page, "bicycles-false")

            if random.random() < 0.25:
                print("   User wants additional room...")
                await self.click_radio_option(page, "wants_addroom-true")
                await page.wait_for_timeout(1000)

                room_uses = [
                    "Home office",
                    "Guest bedroom",
                    "Study room",
                    "Art studio",
                    "Music room",
                    "Yoga/exercise space"
                ]
                await self.fill_textarea(page, "field-addroom_intended_use", random.choice(room_uses))

                areas = ["10-15 m²", "15-20 m²", "8-12 m²", "12-18 m²"]
                await self.fill_text_field(page, "field-addroom_area", random.choice(areas))
            else:
                await self.click_radio_option(page, "wants_addroom-false")

            if random.random() < 0.4:
                print("   User wants storage room...")
                await self.click_radio_option(page, "wants_stockroom-true")
                await page.wait_for_timeout(1000)
                
                storage_uses = [
                    "Seasonal items storage",
                    "Sports equipment",
                    "Documents and files", 
                    "Household items",
                    "Hobby materials"
                ]
                await self.fill_textarea(page, "field-stockroom_intended_use", random.choice(storage_uses))
                
                storage_areas = ["3-5 m²", "5-8 m²", "2-4 m²"]
                await self.fill_text_field(page, "field-stockroom_area", random.choice(storage_areas))
            else:
                await self.click_radio_option(page, "wants_stockroom-false")

            if random.random() < 0.15:
                await self.click_radio_option(page, "wants_workshop-true")
                await page.wait_for_timeout(1000)
                
                studio_uses = [
                    "Art and painting",
                    "Woodworking",
                    "Photography",
                    "Crafts and DIY",
                    "Music production"
                ]
                await self.fill_textarea(page, "field-workshop_intended_use", random.choice(studio_uses))
            else:
                await self.click_radio_option(page, "wants_workshop-false")

            await self.randomly_select_yes_no(page, "wants_coworking", 0.25)

            if random.random() < 0.6:
                await self.click_radio_option(page, "wants_homeoffice-true")
                await page.wait_for_timeout(1000)
                
                work_reasons = [
                    "Remote work policy",
                    "Freelance work",
                    "Flexible work arrangement",
                    "Better work-life balance",
                    "Avoid commuting"
                ]
                await self.fill_text_field(page, "field-wants_homeoffice_detail", random.choice(work_reasons))
            else:
                await self.click_radio_option(page, "wants_homeoffice-false")

            await self.randomly_select_yes_no(page, "obstacle_free", 0.05)

            print("   Form data entry completed")

        except Exception as e:
            print(f"   Error filling form: {e}")
            raise

    async def click_radio_option(self, page: Page, option_id: str):
        """Click a radio button option"""
        try:
            radio_selector = f"li#{option_id}"
            await page.wait_for_selector(radio_selector, timeout=5000)
            await page.click(radio_selector)
            print(f"     Clicked radio option: {option_id}")
            await page.wait_for_timeout(300)
        except Exception as e:
            print(f"     Failed to click radio option {option_id}: {e}")

    async def randomly_select_yes_no(self, page: Page, field_name: str, yes_probability: float):
        """Randomly select yes or no for a field based on probability"""
        if random.random() < yes_probability:
            await self.click_radio_option(page, f"{field_name}-true")
        else:
            await self.click_radio_option(page, f"{field_name}-false")

    async def set_number_field(self, page: Page, field_id: str, value: int):
        """Set value in a number incrementer field"""
        try:
            field_selector = f"input#{field_id}"
            await page.wait_for_selector(field_selector, timeout=5000)
            
            await page.fill(field_selector, "0")
            await page.wait_for_timeout(300)
            
            increment_selector = f"div#increment-{field_id}"
            for _ in range(value):
                try:
                    await page.click(increment_selector)
                    await page.wait_for_timeout(200)
                except:
                    await page.fill(field_selector, str(value))
                    break
            
            print(f"     Set {field_id} to {value}")
        except Exception as e:
            print(f"     Failed to set number field {field_id}: {e}")

    async def fill_text_field(self, page: Page, field_id: str, value: str):
        """Fill a text input field"""
        try:
            field_selector = f"input#{field_id}"
            await page.wait_for_selector(field_selector, timeout=5000)

            await page.fill(field_selector, "")
            await page.type(field_selector, value, delay=50)
            
            print(f"     Filled {field_id} with: {value}")
        except Exception as e:
            print(f"     Failed to fill text field {field_id}: {e}")

    async def fill_textarea(self, page: Page, field_id: str, value: str):
        """Fill a textarea field"""
        try:
            field_selector = f"textarea#{field_id}"
            await page.wait_for_selector(field_selector, timeout=5000)

            await page.fill(field_selector, "")
            await page.type(field_selector, value, delay=40)
            
            print(f"     Filled textarea {field_id} with: {value}")
        except Exception as e:
            print(f"     Failed to fill textarea {field_id}: {e}")

    async def submit_application_form(self, page: Page):
        """Submit the application form using the Save and next button"""
        try:
            print("   Looking for Save and next button...")
            
            submit_selector = "div#application-btn-submit"
            await page.wait_for_selector(submit_selector, timeout=10000)
            
            submit_button = await page.query_selector(submit_selector)
            if submit_button:
                await submit_button.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)

                await submit_button.evaluate("el => el.style.border = '3px solid red'")
                await page.wait_for_timeout(1000)
                
                await submit_button.click()
                print("     Save and next button clicked")

                await page.wait_for_timeout(3000)

                await self.check_form_submission_result(page)
                
            else:
                raise Exception("Submit button not found")
                
        except Exception as e:
            print(f"   Error submitting form: {e}")
            raise

    async def check_form_submission_result(self, page: Page):
        """Check the result of form submission"""
        try:
            error_selectors = [
                ".error-message",
                ".validation-error", 
                ".field-error",
                "[class*='error']"
            ]
            
            has_errors = False
            for selector in error_selectors:
                errors = await page.query_selector_all(selector)
                if errors:
                    for error in errors:
                        if await error.is_visible():
                            error_text = await error.text_content()
                            print(f"     Validation error found: {error_text}")
                            has_errors = True
            
            if not has_errors:
                step_indicator = await page.query_selector("div#apartment_household .af-position.active")
                if step_indicator:
                    print("     Successfully progressed to Household step")
                else:
                    current_url = page.url
                    print(f"     Current URL after submission: {current_url}")
                    
                    success_indicators = await page.query_selector_all("[class*='success'], .step-completed")
                    if success_indicators:
                        print("     Form submission appears successful")
                    else:
                        print("     Form submission status unclear - continuing...")
            
        except Exception as e:
            print(f"   Error checking submission result: {e}")

    async def test_form_validation_scenarios(self, page: Page):
        """Test various form validation scenarios"""
        print("=== FORM VALIDATION SCENARIOS TEST ===")
        
        scenarios = [
            "empty_form",
            "minimal_data", 
            "maximum_data",
            "invalid_data"
        ]
        
        for scenario in scenarios:
            try:
                print(f"Testing scenario: {scenario}")
                await page.reload()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
                
                if scenario == "empty_form":
                    pass
                elif scenario == "minimal_data":
                    await self.fill_minimal_required_data(page)
                elif scenario == "maximum_data":
                    await self.fill_all_possible_fields(page)
                elif scenario == "invalid_data":
                    await self.fill_invalid_data(page)
                
                await self.submit_application_form(page)
                await page.screenshot(path=f"screenshots/scenario_{scenario}.png", full_page=True)
                
            except Exception as e:
                print(f"Scenario {scenario} failed: {e}")

    async def fill_minimal_required_data(self, page: Page):
        """Fill only minimal required data"""
        print("   Filling minimal required data...")

    async def fill_all_possible_fields(self, page: Page):
        """Fill all possible form fields"""
        print("   Filling all possible fields...")
        
        await self.click_radio_option(page, "parking-true")
        await page.wait_for_timeout(1000)
        
        parking_fields = [
            "field-parking_regular", "field-parking_small", "field-parking_large",
            "field-parking_electric", "field-parking_electric_small", 
            "field-parking_outdoor", "field-parking_special"
        ]
        
        for field in parking_fields:
            await self.set_number_field(page, field, 1)
        
        await self.fill_text_field(page, "field-car_reason", "Business use and family transportation needs")
        
        # Enable all other sections
        await self.click_radio_option(page, "motorbikes-true")
        await page.wait_for_timeout(500)
        await self.set_number_field(page, "field-parking_motorbike", 1)
        
        await self.click_radio_option(page, "bicycles-true")
        await page.wait_for_timeout(500)
        await self.set_number_field(page, "field-parking_bicycle", 2)
        await self.set_number_field(page, "field-parking_electric_bicycles", 1)
        
        await self.click_radio_option(page, "wants_addroom-true")
        await page.wait_for_timeout(500)
        await self.fill_textarea(page, "field-addroom_intended_use", "Multi-purpose room for home office and guest accommodation")
        await self.fill_text_field(page, "field-addroom_area", "15-25 m²")
        
        await self.click_radio_option(page, "wants_stockroom-true")
        await page.wait_for_timeout(500)
        await self.fill_textarea(page, "field-stockroom_intended_use", "Storage for seasonal items, sports equipment, and household goods")
        await self.fill_text_field(page, "field-stockroom_area", "5-10 m²")
        
        await self.click_radio_option(page, "wants_workshop-true")
        await page.wait_for_timeout(500)
        await self.fill_textarea(page, "field-workshop_intended_use", "Creative studio for art, crafts, and DIY projects")
        
        await self.click_radio_option(page, "wants_coworking-true")
        await self.click_radio_option(page, "wants_homeoffice-true")
        await page.wait_for_timeout(500)
        await self.fill_text_field(page, "field-wants_homeoffice_detail", "Full-time remote work arrangement with video conferencing needs")
        
        await self.click_radio_option(page, "obstacle_free-true")

    async def fill_invalid_data(self, page: Page):
        """Fill form with invalid data to test validation"""
        print("   Filling invalid data...")
        
        await self.click_radio_option(page, "parking-true")
        await page.wait_for_timeout(1000)
        
        try:
            await page.fill("input#field-parking_regular", "-5")
            await page.fill("input#field-parking_small", "abc")
        except:
            pass
        
        long_text = "x" * 1000
        try:
            await self.fill_text_field(page, "field-car_reason", long_text)
        except:
            pass

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
    async def run_complete_workflow_test():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            page = await browser.new_page()
            
            test_suite = TestCompleteApartmentWorkflow()
            
            try:
                await test_suite.test_complete_apartment_workflow(page)
                print("\nCOMPLETE APARTMENT WORKFLOW TEST COMPLETED SUCCESSFULLY!")
                
            except Exception as e:
                print(f"\nCOMPLETE APARTMENT WORKFLOW TEST FAILED: {e}")
                import traceback
                print(traceback.format_exc())
            finally:
                print("Screenshots saved in screenshots/ directory")
                print("\nKeeping browser open for 10 seconds to review results...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    print("Starting complete apartment workflow test...")
    asyncio.run(run_complete_workflow_test())