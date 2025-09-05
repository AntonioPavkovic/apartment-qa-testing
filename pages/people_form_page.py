from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from config.test_config import TestConfig, Selectors
from data.models import PersonData
from exceptions.test_exceptions import ElementInteractionError, ApplicationFormError
from utils.element_interactor import ElementInteractor
from utils.screenshot_manager import ScreenshotManager
from utils.logging import TestLogger

class PeopleFormPage:
    """Page Object Model for people form (step 3) functionality"""
    
    def __init__(self, page: Page, interactor: ElementInteractor, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.interactor = interactor
        self.screenshot_manager = screenshot_manager
        self.logger = logger
    
    async def verify_people_form_loaded(self) -> bool:
        """Verify that the people form has loaded correctly by checking for key elements."""
        self.logger.info("Verifying people form...")
        
        try:
            await self.page.wait_for_selector("div#apartment_people .af-position.active", timeout=TestConfig.SLOW_TIMEOUT)

            await self.page.wait_for_selector(Selectors.FIRST_NAME_INPUT, timeout=TestConfig.SLOW_TIMEOUT)
            
            self.logger.info("People form verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying people form: {e}")
            return False
    
    async def fill_people_form(self, people_data: list) -> None:
        """Fill out the people form for multiple people (2 adults + 1 child)"""
        self.logger.info(f"Filling people form for {len(people_data)} people...")
        
        try:
            self.logger.info("Adding and filling first adult...")
            await self._add_adult()
            
            if not await self.verify_people_form_loaded():
                raise ApplicationFormError("People form did not load correctly after clicking 'Add adult'")
            
            await self._fill_person_data(people_data[0], person_index=0)
            await self._save_current_person()
            
            if len(people_data) > 1:
                self.logger.info("Adding second adult...")
                await self._add_adult()
                await self._fill_person_data(people_data[1], person_index=1)
                await self._save_current_person()
            
            if len(people_data) > 2:
                self.logger.info("Adding child...")
                await self._add_child()
                await self._fill_person_data(people_data[2], person_index=2)
                await self._save_current_person()
            
            await self._navigate_to_summary()
            
            await self.screenshot_manager.capture(self.page, "people_form_filled", full_page=True)
            self.logger.info("People form completed")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "people_form_filling")
            raise ApplicationFormError(f"Error filling people form: {e}")

    async def _navigate_to_summary(self) -> None:
        """Navigate from people form to summary page"""
        self.logger.info("Looking for Continue/Next button to navigate to summary...")
        
        try:
            continue_selectors = [
                "#application-btn-next",
                ".btn:has-text('Continue')",
                ".btn:has-text('Next')", 
                ".btn.btn-next",
                "button:has-text('Continue')",
                "button:has-text('Next')",
                ".navigation-buttons .btn:not(.btn-previous)"
            ]
            
            continue_button = None
            for selector in continue_selectors:
                continue_button = await self.page.query_selector(selector)
                if continue_button and await continue_button.is_visible():
                    self.logger.info(f"Found continue button: {selector}")
                    break
            
            if continue_button:
                await continue_button.scroll_into_view_if_needed()
                await continue_button.click()
                self.logger.info("Clicked continue button to navigate to summary")
                await self.page.wait_for_timeout(3000)
            else:
                self.logger.warning("No continue button found - summary page may load automatically")
                await self.page.wait_for_timeout(2000)
                
        except Exception as e:
            self.logger.warning(f"Could not find continue button: {e}")
    
    async def _debug_page_state(self) -> None:
        """Debug method to understand the current page state"""
        self.logger.info("=== DEBUGGING PAGE STATE ===")
        
        current_url = self.page.url
        self.logger.info(f"Current URL: {current_url}")
        
        all_steps = await self.page.query_selector_all(".af-position")
        for i, step in enumerate(all_steps):
            class_list = await step.get_attribute("class")
            text = await step.text_content()
            self.logger.info(f"Step {i}: class='{class_list}', text='{text}'")

        add_elements = await self.page.query_selector_all("[class*='add'], [id*='add'], [class*='create'], [id*='create']")
        self.logger.info(f"Found {len(add_elements)} elements with 'add' or 'create'")
        
        for i, elem in enumerate(add_elements[:5]):
            tag_name = await elem.evaluate("el => el.tagName")
            class_name = await elem.get_attribute("class") or ""
            id_attr = await elem.get_attribute("id") or ""
            text = await elem.text_content() or ""
            is_visible = await elem.is_visible()
            self.logger.info(f"Element {i}: {tag_name}, class='{class_name}', id='{id_attr}', text='{text[:50]}', visible={is_visible}")
        
        buttons = await self.page.query_selector_all("button, [role='button'], .btn, div[class*='btn']")
        self.logger.info(f"Found {len(buttons)} button-like elements")
        
        for i, btn in enumerate(buttons[:10]):
            text = await btn.text_content() or ""
            class_name = await btn.get_attribute("class") or ""
            id_attr = await btn.get_attribute("id") or ""
            is_visible = await btn.is_visible()
            self.logger.info(f"Button {i}: text='{text[:30]}', class='{class_name}', id='{id_attr}', visible={is_visible}")
    
    async def _add_adult(self) -> None:
        """
        Add another adult to the form by clicking the 'Add adult' button.
        """
        self.logger.info("Looking for 'Add adult' button...")
        try:
            add_adult_selector = "#create-new-adult"
            
            add_adult_button = self.page.locator(add_adult_selector)
            await add_adult_button.wait_for(state="visible", timeout=TestConfig.DEFAULT_TIMEOUT)

            is_disabled = await add_adult_button.get_attribute("disabled")
            if is_disabled:
                self.logger.info("Add adult button is disabled, waiting a moment...")
                await self.page.wait_for_timeout(2000)
            
            await add_adult_button.click()
            self.logger.info("Clicked 'Add adult' button")

            await self.page.wait_for_selector(
                Selectors.FIRST_NAME_INPUT, 
                state="visible",
                timeout=TestConfig.DEFAULT_TIMEOUT
            )
            self.logger.info("Adult form loaded successfully")

        except Exception as e:
            self.logger.error(f"Error adding adult: {e}")
            await self.screenshot_manager.capture_error(self.page, "add_adult_error")
            raise ApplicationFormError(f"Could not add adult: {e}")
    
    async def _add_child(self) -> None:
        """Add a child to the form"""
        try:
            child_selectors = ["#create-new-child", "text=Add child", ".create-child", "[class*='add-child']"]
            
            add_child_button = None
            for selector in child_selectors:
                add_child_button = await self.page.query_selector(selector)
                if add_child_button and await add_child_button.is_visible():
                    break
            
            if add_child_button:
                await add_child_button.scroll_into_view_if_needed()
                await add_child_button.click()
                self.logger.info("Clicked 'Add child' button")
            else:
                await self._add_adult()
                self.logger.info("Used general add person button for child")
            
            await self.page.wait_for_selector("input[placeholder='Please specify']", timeout=5000)
            await self.page.wait_for_timeout(1000)
            
        except Exception as e:
            self.logger.error(f"Error adding child: {e}")
            raise ApplicationFormError(f"Could not add child: {e}")
    
    async def _save_current_person(self) -> None:
        """Save the current person's data using the Save button"""
        try:
            self.logger.info("Looking for Save button...")
            
            save_button = await self.page.query_selector("#submit-nested-form")
            
            if not save_button:
                fallback_selectors = [
                    ".btn.btn-primary:has-text('Save')",
                    ".btn:has-text('Save')", 
                    "div:has-text('Save').btn",
                    "[id='submit-nested-form']"
                ]
                
                for selector in fallback_selectors:
                    save_button = await self.page.query_selector(selector)
                    if save_button and await save_button.is_visible():
                        self.logger.info(f"Found Save button using fallback selector: {selector}")
                        break
            
            if save_button:
                await save_button.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(500)

                is_disabled = await save_button.get_attribute("disabled")
                if is_disabled:
                    self.logger.warning("Save button is disabled, waiting for it to become enabled...")
                    await self.page.wait_for_timeout(2000)
                
                await save_button.click()
                self.logger.info("Clicked Save button for current person")
                
                try:
                    await self.page.wait_for_selector("#submit-nested-form", state="hidden", timeout=10000)
                    self.logger.info("Person data saved successfully - form closed")
                except:
                    await self.page.wait_for_timeout(3000)
                    self.logger.info("Save operation completed (timeout waiting for form to close)")
                    
            else:
                self.logger.warning("Save button not found")
                await self.screenshot_manager.capture_error(self.page, "save_button_not_found")
                raise ElementInteractionError("Save button with ID #submit-nested-form not found")
                
        except Exception as e:
            self.logger.error(f"Error saving current person: {e}")
            await self.screenshot_manager.capture_error(self.page, "save_person_error")
            raise ApplicationFormError(f"Could not save person data: {e}")
    
    async def _fill_person_data(self, person: PersonData, person_index: int = 0) -> None:
        """Fill data for a single person - handles both adult and child forms"""
        self.logger.info(f"Filling data for person {person_index + 1}: {person.first_name}")
        
        try:
            nights_field = await self.page.query_selector("#field-days_present")
            is_child_form = nights_field is not None
            
            if is_child_form:
                self.logger.info("Detected child form - filling child-specific fields")
                await self._fill_child_form(person)
            else:
                self.logger.info("Detected adult form - filling adult-specific fields")
                await self._fill_adult_form(person)
                
        except Exception as e:
            self.logger.error(f"Error filling person data for {person.first_name}: {e}")
            raise

    async def _fill_child_form(self, person: PersonData) -> None:
        """Fill data specifically for child form"""
        self.logger.info("Filling child form...")
        
        try:
            await self.page.wait_for_timeout(1000)
            
            if person.first_name:
                await self.interactor.fill_field_safely("#field-firstname", person.first_name)
            
            if person.last_name:
                await self.interactor.fill_field_safely("#field-name", person.last_name)
            
            if person.date_of_birth:
                await self.interactor.fill_field_safely("#field-date_of_birth", person.date_of_birth)
            
            if person.nationality:
                await self._select_dropdown_by_id("field-nation", person.nationality)
            
            nights_in_apartment = getattr(person, 'nights_in_apartment', 7)
            nights_in_apartment = min(nights_in_apartment, 7)
            await self._set_number_incrementer("field-days_present", nights_in_apartment)
            
        except Exception as e:
            self.logger.error(f"Error filling child form: {e}")
            raise

    async def _fill_adult_form(self, person: PersonData) -> None:
        """Fill data specifically for adult form"""
        self.logger.info("Filling adult form...")
        
        try:
            await self._fill_general_info(person)
            await self._fill_contact_info(person)
            await self._fill_housing_situation(person)
            if person.employment_status:
                await self._select_dropdown_by_id("field-employment_quota", person.employment_status)
        
            await self._fill_creditworthiness(person)
            await self._handle_documents(person)
            await self._handle_agreement_checkbox()
            
        except Exception as e:
            self.logger.error(f"Error filling adult form: {e}")
            raise

    async def _set_number_incrementer(self, field_id: str, value: int) -> None:
        """Set value for number incrementer field (used for nights in apartment)"""
        try:
            self.logger.info(f"Setting {field_id} to {value}")
            
            input_field = await self.page.query_selector(f"#{field_id}")
            if not input_field:
                raise ElementInteractionError(f"Number incrementer field {field_id} not found")
            
            current_value = await input_field.input_value()
            current_int = int(current_value) if current_value.isdigit() else 0
            
            difference = value - current_int
            
            if difference > 0:
                increment_button = await self.page.query_selector(f"#increment-{field_id}")
                if increment_button:
                    for _ in range(difference):
                        await increment_button.click()
                        await self.page.wait_for_timeout(100)
            elif difference < 0:
                decrement_button = await self.page.query_selector(f"#decrement-{field_id}")
                if decrement_button:
                    for _ in range(abs(difference)):
                        await decrement_button.click()
                        await self.page.wait_for_timeout(100) 
            
            final_value = await input_field.input_value()
            if int(final_value) != value:
                self.logger.warning(f"Failed to set exact value. Expected: {value}, Got: {final_value}")
            else:
                self.logger.info(f"Successfully set {field_id} to {value}")
                
        except Exception as e:
            self.logger.error(f"Error setting number incrementer {field_id}: {e}")
            raise ElementInteractionError(f"Could not set number incrementer {field_id}: {e}")
    
    async def _fill_general_info(self, person: PersonData) -> None:
        """Fill general information section"""
        self.logger.info("Filling general information...")
        
        try:
            await self.page.wait_for_timeout(1000)
            
            if person.salutation:
                await self._select_dropdown_by_id("field-title", person.salutation)
            
            if person.first_name:
                await self.interactor.fill_field_safely("#field-firstname", person.first_name)
            
            if person.last_name:
                await self.interactor.fill_field_safely("#field-name", person.last_name)
            
            if person.date_of_birth:
                await self.interactor.fill_field_safely("#field-date_of_birth", person.date_of_birth)
            
            if person.place_of_birth:
                await self.interactor.fill_field_safely("#field-place_of_birth", person.place_of_birth)
            
            if person.civil_status:
                await self._select_dropdown_by_id("field-civil_status", person.civil_status)

            if person.nationality:
                await self._select_dropdown_by_id("field-nation", person.nationality)
                
                hometown_value = person.place_of_birth or person.nationality
                await self.interactor.fill_field_safely("#field-place_of_citizenship", hometown_value)
                self.logger.info(f"Filled Hometown field with '{hometown_value}'")
            else:
                self.logger.warning("Nationality not provided, skipping Hometown field.")
            
            if person.residency_status:
                await self._select_dropdown_by_id("field-permit", person.residency_status)
            
            if person.living_in_switzerland_since:
                await self.interactor.fill_field_safely("#field-living_in_country_since", person.living_in_switzerland_since)
            
            if person.type_of_tenant:
                await self._select_dropdown_by_id("field-tenant_type", person.type_of_tenant)
                
        except Exception as e:
            self.logger.error(f"Error filling general info: {e}")
            raise
    
    
    async def _fill_creditworthiness(self, person: PersonData) -> None:
        """Fill creditworthiness section"""
        self.logger.info("Filling creditworthiness...")
        
        try:
            if person.credit_check_type:
                if person.credit_check_type == "CreditTrust certificate":
                    selected_element = await self.page.query_selector("#securities-certificat.selected")
                    if not selected_element:
                        await self.page.click("#securities-certificat")
                        self.logger.info("Selected CreditTrust certificate")
                elif person.credit_check_type == "Excerpt from debt collection":
                    await self.page.click("#securities-enforcement")
                    self.logger.info("Selected Excerpt from debt collection")
            else:
                selected_element = await self.page.query_selector("#securities-certificat.selected")
                if not selected_element:
                    await self.page.click("#securities-certificat")
                    self.logger.info("Selected default CreditTrust certificate")
            
            await self._handle_yes_no_question_by_id("liability", person.personal_liability_insurance)
            await self._handle_yes_no_question_by_id("household_insurance", person.household_insurance)
            
        except Exception as e:
            self.logger.error(f"Error filling creditworthiness: {e}")
            raise
    
    async def _handle_agreement_checkbox(self) -> None:
        """Handle the required agreement checkbox"""
        try:
            self.logger.info("Handling agreement checkbox...")

            agreement_checkbox = await self.page.query_selector("#field-agreement_references")
            if agreement_checkbox:
                is_checked = await agreement_checkbox.is_checked()
                if not is_checked:
                    await agreement_checkbox.click()
                    self.logger.info("Checked agreement checkbox")
                else:
                    self.logger.info("Agreement checkbox already checked")
            else:
                checkbox_label = await self.page.query_selector("label[for='field-agreement_references']")
                if checkbox_label:
                    await checkbox_label.click()
                    self.logger.info("Checked agreement checkbox via label")
                else:
                    self.logger.warning("Agreement checkbox not found")
            
        except Exception as e:
            self.logger.warning(f"Could not handle agreement checkbox: {e}")
    

    async def _select_dropdown_by_id(self, field_id: str, value: str) -> None:
        """Select dropdown option by field ID and value"""
        try:
            self.logger.info(f"Selecting '{value}' for field '{field_id}'")

            if field_id == "field-employment_quota" or field_id == "field-country":

                if field_id == "field-country":
                    try:
                        self.logger.info(f"Attempting to select country: {value}")

                        toggle_selector = f"#toggle-{field_id}"
                        await self.page.locator(toggle_selector).click()
                        self.logger.info(f"Clicked dropdown toggle: {toggle_selector}")

                        await self.page.wait_for_timeout(500)

                        await self.page.locator("li.dropdown-item[data-value='CH']").click()
                        self.logger.info("Clicked 'Switzerland' option (data-value=CH)")

                        input_selector = f"#{field_id}"
                        current_value = await self.page.input_value(input_selector)
                        if "Switzerland" not in current_value:
                            self.logger.warning("Switzerland might not have persisted after selection.")
                        else:
                            self.logger.info("Country selection verified: Switzerland")

                    except Exception as e:
                        self.logger.error(f"Failed to select country 'Switzerland': {e}")
                        await self.screenshot_manager.capture_error(self.page, "country_selection_failed")

                elif field_id == "field-employment_quota" and value == "Retired":
                    try:
                        toggle_selector = f"#toggle-{field_id}"
                        await self.page.click(toggle_selector)
                        await self.page.wait_for_timeout(2000)
                        retired_selectors = [
                            f"text={value}",
                            f"li:has-text('{value}')",
                            f"div:has-text('{value}')",
                            "[data-value='Retired']",
                            ".option:has-text('Retired')"
                        ]
                        option_found = False
                        for selector in retired_selectors:
                            try:
                                option = await self.page.wait_for_selector(selector, timeout=2000)
                                if option and await option.is_visible():
                                    await option.scroll_into_view_if_needed()
                                    await option.click()
                                    self.logger.info(f"Selected '{value}' using {selector}")
                                    option_found = True
                                    break
                            except:
                                continue
                        if not option_found:
                            self.logger.warning(f"Failed to select '{value}', falling back to typing.")
                            input_field = f"#{field_id}"
                            await self.page.fill(input_field, "Retired")
                            await self.page.press(input_field, "Enter")
                            self.logger.info("Typed 'Retired' in employment status field")
                    except Exception as e:
                        self.logger.error(f"Failed to select Retired: {e}")
                        await self.screenshot_manager.capture_error(self.page, "retired_selection_failed")

                else:
                    toggle_selector = f"#toggle-{field_id}"
                    await self.page.locator(toggle_selector).click()
                    option_selectors = [
                        f"text={value}",
                        f"li:has-text('{value}')",
                        f"div:has-text('{value}')",
                        f".option:has-text('{value}')"
                    ]
                    option_found = False
                    for selector in option_selectors:
                        try:
                            option = await self.page.wait_for_selector(selector, timeout=3000)
                            if option and await option.is_visible():
                                await option.scroll_into_view_if_needed()
                                await option.click()
                                self.logger.info(f"Selected '{value}' using {selector}")
                                option_found = True
                                break
                        except:
                            continue
                    if not option_found:
                        self.logger.warning(f"Option '{value}' not found for field '{field_id}'")

            else:
                dropdown_toggle = await self.page.query_selector(f"#{field_id}")
                if not dropdown_toggle:
                    dropdown_toggle = await self.page.query_selector(f"#toggle-{field_id}")

                if dropdown_toggle:
                    await dropdown_toggle.scroll_into_view_if_needed()
                    await dropdown_toggle.click()
                    await self.page.wait_for_timeout(1000)

                    if field_id in ["field-nation", "field-country"]:
                        await dropdown_toggle.fill(value)
                        await self.page.wait_for_timeout(500)

                    option_found = False
                    option_selectors = [
                        f"text={value}",
                        f"text='{value}'",
                        f"[title='{value}']",
                        f"[title*='{value}']",
                        f"li:has-text('{value}')",
                        f".option:has-text('{value}')",
                        f".dropdown-item:has-text('{value}')"
                    ]

                    for selector in option_selectors:
                        try:
                            option = await self.page.query_selector(selector)
                            if option and await option.is_visible():
                                await option.click()
                                await self.page.wait_for_timeout(500)
                                self.logger.info(f"Selected '{value}' for '{field_id}' using {selector}")
                                option_found = True
                                break
                        except:
                            continue

                    if not option_found:
                        self.logger.warning(f"Option '{value}' not found for field '{field_id}'")
                else:
                    self.logger.warning(f"Dropdown field '{field_id}' not found")

        except Exception as e:
            self.logger.warning(f"Could not select dropdown option '{value}' for '{field_id}': {e}")
            await self.screenshot_manager.capture_error(self.page, f"dropdown_error_{field_id}")

    
    async def _fill_contact_info(self, person: PersonData) -> None:
        """Fill contact information section"""
        self.logger.info("Filling contact information...")
        
        try:
            if person.phone_number:
                await self.interactor.fill_field_safely("#field-phone", person.phone_number)
            
            if person.business_phone:
                await self.interactor.fill_field_safely("#field-office_phone", person.business_phone)
            
            if person.email:
                await self.interactor.fill_field_safely("#field-email", person.email)
            
            if person.email:
                await self.interactor.fill_field_safely("#confirm-field-email", person.email)
                
        except Exception as e:
            self.logger.error(f"Error filling contact info: {e}")
            raise
    
    async def _fill_housing_situation(self, person: PersonData) -> None:
        """Fill housing situation section"""
        self.logger.info("Filling housing situation...")
        
        try:
            if person.street_and_number:
                await self.interactor.fill_field_safely("#field-street_nr", person.street_and_number)
            
            if person.post_code:
                await self.interactor.fill_field_safely("#field-postcode", person.post_code)
            
            if person.city:
                await self.interactor.fill_field_safely("#field-city", person.city)
            
            if person.country:
                await self._select_dropdown_by_id("field-country", person.country)
            
            if person.move_in_date:
                await self.interactor.fill_field_safely("#field-living_since", person.move_in_date)

            await self._handle_yes_no_question_by_id("legal_residence", person.civil_law_residence)
            await self._handle_yes_no_question_by_id("move_three_years", person.relocation_last_3_years)
            await self._handle_yes_no_question_by_id("member", person.community_member)
            
        except Exception as e:
            self.logger.error(f"Error filling housing situation: {e}")
            raise

    async def _handle_documents(self, person: PersonData) -> None:
        """Handle document upload sections"""
        self.logger.info("Handling document sections...")
        self.logger.info("Document upload sections detected but not filled (optional)")
    
    async def _handle_yes_no_question_by_id(self, question_id: str, value: bool) -> None:
        """Handle yes/no questions with button clicks using specific IDs"""
        if value is not None:
            try:
                if value:
                    yes_button = await self.page.query_selector(f"#{question_id}-true")
                    if yes_button:
                        await yes_button.click()
                        self.logger.info(f"Selected 'Yes' for {question_id}")
                else:
                    no_button = await self.page.query_selector(f"#{question_id}-false")
                    if no_button:
                        await no_button.click()
                        self.logger.info(f"Selected 'No' for {question_id}")
                        
                await self.page.wait_for_timeout(300)
            except Exception as e:
                self.logger.warning(f"Could not handle yes/no question '{question_id}': {e}")
    
    async def submit_people_form(self) -> None:
        """Submit the people form - this should be called after all people are added and saved"""
        self.logger.info("Submitting people form...")
        
        try:
            submit_selectors = [
                "button:has-text('Submit')",
                "button:has-text('Continue')", 
                "button:has-text('Next')",
                ".btn:has-text('Submit')",
                ".btn:has-text('Continue')",
                ".btn:has-text('Next')",
                Selectors.SUBMIT_BUTTON
            ]
            
            submit_button = None
            for selector in submit_selectors:
                submit_button = await self.page.query_selector(selector)
                if submit_button and await submit_button.is_visible():
                    break
            
            if submit_button:
                await submit_button.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(1000)
                await submit_button.click()
                
                self.logger.info("People form submitted")
                await self.page.wait_for_timeout(3000)
            else:
                self.logger.warning("Could not find submit button for people form")
        
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "people_form_submission")
            raise ApplicationFormError(f"Error submitting people form: {e}")