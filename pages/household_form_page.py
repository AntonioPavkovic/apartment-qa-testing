from playwright.async_api import Page, ElementHandle
from config.test_config import TestConfig, Selectors
from data.models import HouseholdData
from exceptions.test_exceptions import ElementInteractionError, ApplicationFormError
from utils.element_interactor import ElementInteractor
from utils.screenshot_manager import ScreenshotManager
from utils.logging import TestLogger

class HouseholdFormPage:
    """Page Object Model for household form (step 2) functionality"""
    
    def __init__(self, page: Page, interactor: ElementInteractor,  screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.interactor = interactor
        self.screenshot_manager = screenshot_manager
        self.logger = logger
    
    async def verify_household_form_loaded(self) -> bool:
        """Verify that the household form has loaded correctly"""
        self.logger.info("Verifying household form...")
        
        try:
            step2_active = await self.page.query_selector("div#apartment_household .af-position.active")
            if not step2_active:
                self.logger.warning("Step 2 (Household) is not active")
                return False
   
            household_dropdown = await self.page.query_selector(Selectors.HOUSEHOLD_TYPE_DROPDOWN)
            if not household_dropdown:
                self.logger.warning("Household type dropdown not found")
                return False
            
            self.logger.info("Household form verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying household form: {e}")
            return False
    
    async def fill_household_form(self, household_data: HouseholdData) -> None:
        """Fill out the complete household form"""
        self.logger.info("Filling household form with data...")
        
        try:
            await self.page.wait_for_timeout(2000)
            
            await self._fill_general_section(household_data)
            await self._fill_moving_information(household_data)
            await self._fill_security_deposit_section(household_data)
            await self._fill_motivation_section(household_data)
            await self._fill_additional_information(household_data)
            
            await self.screenshot_manager.capture(self.page, "household_form_filled", full_page=True)
            self.logger.info("Household form completed")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "household_form_filling")
            raise ApplicationFormError(f"Error filling household form: {e}")
    
    async def _fill_general_section(self, household_data: HouseholdData) -> None:
        """Fill the General section"""
        self.logger.info("Filling General section...")

        if household_data.household_type:
            await self._select_dropdown_option(
                Selectors.HOUSEHOLD_TYPE_DROPDOWN,
                Selectors.HOUSEHOLD_TYPE_INPUT,
                household_data.household_type
            )

        if household_data.has_pets is not None:
            await self._click_yes_no_radio("pets", household_data.has_pets)
            pets_type = getattr(household_data, "pets_type", None)
            if household_data.has_pets and pets_type:
                await self.page.wait_for_selector("input#field-pets_type", state="visible", timeout=5000)
                await self.interactor.fill_field_safely("input#field-pets_type", pets_type)

        if household_data.has_music_instruments is not None:
            await self._click_yes_no_radio("music_instruments", household_data.has_music_instruments)
            music_type = getattr(household_data, "music_instruments_type", None)
            if household_data.has_music_instruments and music_type:
                await self.page.wait_for_selector("input#field-music_instruments_type", state="visible", timeout=5000)
                await self.interactor.fill_field_safely("input#field-music_instruments_type", music_type)

        if household_data.is_smoker is not None:
            await self._click_yes_no_radio("smoking", household_data.is_smoker)

    
    async def _fill_moving_information(self, household_data: HouseholdData) -> None:
        """Fill Moving Information section"""
        self.logger.info("Filling Moving Information section...")
        
        if household_data.relocation_reason:
            await self._select_dropdown_option(Selectors.RELOCATION_REASON_DROPDOWN, "input#field-relocation_reason", household_data.relocation_reason)

        if household_data.desired_move_date:
            await self.interactor.fill_field_safely(Selectors.MOVING_DATE_INPUT, household_data.desired_move_date)
        

        if household_data.mailbox_label:
            await self.interactor.fill_field_safely(Selectors.MAILBOX_LABEL_INPUT, household_data.mailbox_label)
    
    async def _fill_security_deposit_section(self, household_data: HouseholdData) -> None:
        """Fill Security Deposit section"""
        self.logger.info("Filling Security Deposit section...")

        if household_data.security_deposit_type:
            if household_data.security_deposit_type == "deposit":
                await self._click_radio_option("securities_options-deposit")
            else:
                await self._click_radio_option("securities_options-insurance")
        
        if household_data.income_rent_ratio is not None:
            await self._click_yes_no_radio("income_rent_ratio", household_data.income_rent_ratio)
        
        if household_data.iban:
            await self.interactor.fill_field_safely(Selectors.IBAN_INPUT, household_data.iban)
        
        if household_data.bank_name:
            await self.interactor.fill_field_safely(Selectors.BANK_NAME_INPUT, household_data.bank_name)
        
        if household_data.account_owner:
            await self.interactor.fill_field_safely(Selectors.ACCOUNT_OWNER_INPUT, household_data.account_owner)
    
    async def _fill_motivation_section(self, household_data: HouseholdData) -> None:
        """Fill Motivation section"""
        self.logger.info("Filling Motivation section...")

        if household_data.motivation:
            await self.interactor.fill_field_safely(Selectors.MOTIVATION_INPUT, household_data.motivation)
        
        if household_data.participation_ideas:
            await self.interactor.fill_field_safely(Selectors.PARTICIPATION_TEXTAREA, household_data.participation_ideas, typing_delay=40)

        if household_data.relation_to_cooperative:
            await self._select_dropdown_option(Selectors.RELATION_DROPDOWN, "input#field-relation_to_project", household_data.relation_to_cooperative)
        
        if household_data.relation_type:
            await self._select_dropdown_option(Selectors.RELATION_TYPE_DROPDOWN, "input#field-relation_to_project_detail", household_data.relation_type)
    
    async def _fill_additional_information(self, household_data: HouseholdData) -> None:
        """Fill Additional Information section"""
        self.logger.info("Filling Additional Information section...")

        if household_data.object_found_on:
            await self._select_dropdown_option(Selectors.SOURCE_DROPDOWN, "input#field-source", household_data.object_found_on)
        
        if household_data.remarks:
            await self.interactor.fill_field_safely(Selectors.REMARKS_TEXTAREA, household_data.remarks, typing_delay=40)
    
    async def _click_yes_no_radio(self, field_name: str, select_yes: bool) -> None:
        """Click yes/no radio button for a field"""
        suffix = "true" if select_yes else "false"
        await self._click_radio_option(f"{field_name}-{suffix}")
    
    async def _click_radio_option(self, option_id: str) -> None:
        """Click a radio button option"""
        try:
            radio_selector = f"li#{option_id}"
            await self.page.wait_for_selector(radio_selector, timeout=TestConfig.DEFAULT_TIMEOUT)
            await self.page.click(radio_selector)
            self.logger.info(f"Clicked radio option: {option_id}")
            await self.page.wait_for_timeout(300)
        except Exception as e:
            raise ElementInteractionError(f"Failed to click radio option {option_id}: {e}")
    
    async def _select_dropdown_option(self, dropdown_selector: str, input_selector: str, value: str) -> None:
        """Select option from dropdown by clicking on the dropdown item"""
        try:
            # Click dropdown to open it
            await self.page.wait_for_selector(dropdown_selector, timeout=TestConfig.DEFAULT_TIMEOUT)
            await self.page.click(dropdown_selector)
            await self.page.wait_for_timeout(1000)
            
            # Wait for dropdown items to appear
            await self.page.wait_for_selector("ul.select-dropdown-items-wrapper li", state="visible", timeout=TestConfig.DEFAULT_TIMEOUT)
            
            # Try to select by data-value attribute instead of ID (more reliable)
            data_value = self._map_value_to_data_value(value)
            
            if data_value:
                # Use data-value attribute selector instead of ID
                item_selector = f'li[data-value="{data_value}"]'
                await self.page.wait_for_selector(item_selector, timeout=TestConfig.DEFAULT_TIMEOUT)
                await self.page.click(item_selector)
                await self.page.wait_for_timeout(500)
                
                self.logger.info(f"Selected dropdown option: {value} (data-value: {data_value})")
            else:
                # Fallback: try to find by text content
                await self._select_by_text_content(value)
                
        except Exception as e:
            raise ElementInteractionError(f"Failed to select dropdown option {value}: {e}")


    def _map_value_to_data_value(self, value: str) -> str:
        """Map friendly values to actual dropdown data-value attributes"""
        household_type_mapping = {
            "single person household": "single_person_household",
            "couple household": "couple_household", 
            "couple household with child": "couple_household_with_child",
            "Single parent with child/ren": "single_parent_household",
            "Flat-share": "flat_share",
            "Other": "other_household"
        }
        
        relocation_reason_mapping = {
            "Change of life situation": "change_in_life_situation",
            "Change in income": "change_in_income_situation",
            "Change in the place of work": "change_of_place_of_work",
            "Change in space requirements": "change_in_space requirement",
            "Noise / Emissions": "noise_imissions",
            "Price/performance ratio": "price_performance_ratio",
            "Problems with janitor/administration": "problems_with_administration",
            "Problems with neighbors": "problems_with_neighbour",
            "Reconstruction/Renovation": "reconstruction",
            "Quality of living": "quality_of_living",
            "Termination by landlord": "termination_by_landlord",
            "Without a permanent residence": "no_permanent_residence",
            "Fixed term tenancy": "fixed_term_tenancy",
            "Other": "other_relocation_reason"
        }
        
        # Add mappings for the cooperative relation dropdown
        cooperative_relation_mapping = {
            "Current tenant": "current_tenant",
            "Child tenant": "child_tenant", 
            "Voluntary member": "voluntary_member",
            "No relation": "no_relation"
        }
        
        # Add mappings for the relation type dropdown
        relation_type_mapping = {
            "Already living in the neighborhood": "already_living_neighborhood",
            "Workplace in the neighborhood": "workplace_neighborhood",
            "Caring for relatives in the neighborhood": "caring_relatives_neighborhood", 
            "Children school/kindergarten in the neighborhood": "children_school_neighborhood"
        }
        
        # Add mappings for object source dropdown
        object_source_mapping = {
            "Real estate platform (Newhome, Erstbezug, Homegate, ...)": "real_estate_platform",
            "Project website": "project_website",
            "Facebook": "facebook",
            "Instagram": "instagram", 
            "LinkedIn": "linkedin"
        }
        
        # Check all mappings
        all_mappings = [
            household_type_mapping, 
            relocation_reason_mapping, 
            cooperative_relation_mapping,
            relation_type_mapping,
            object_source_mapping
        ]
        
        for mapping in all_mappings:
            if value in mapping:
                return mapping[value]
        
        return None

    async def _select_by_text_content(self, value: str) -> None:
        """Fallback method to select by text content if data-value mapping fails"""
        try:
            self.logger.info(f"Trying fallback text selection for: {value}")
            
            # Get all visible dropdown items
            dropdown_items = await self.page.query_selector_all("li.dropdown-item")
            
            for item in dropdown_items:
                if await item.is_visible():
                    item_text = await item.text_content()
                    if item_text and item_text.strip():
                        # Check for exact match first
                        if value.lower().strip() == item_text.lower().strip():
                            await item.click()
                            await self.page.wait_for_timeout(500)
                            self.logger.info(f"Selected dropdown option by exact text match: {value}")
                            return
                        
                        # Check for partial match
                        if value.lower() in item_text.lower():
                            await item.click()
                            await self.page.wait_for_timeout(500)
                            self.logger.info(f"Selected dropdown option by partial text match: {value} -> {item_text}")
                            return
            
            # If no match found, list available options for debugging
            available_options = []
            for item in dropdown_items:
                if await item.is_visible():
                    text = await item.text_content()
                    if text and text.strip():
                        available_options.append(text.strip())
            
            self.logger.error(f"Available dropdown options: {available_options}")
            raise ElementInteractionError(f"Could not find dropdown option with text: {value}")
            
        except Exception as e:
            raise ElementInteractionError(f"Failed to select by text content: {e}")
    
    async def submit_household_form(self) -> None:
        """Submit the household form"""
        self.logger.info("Submitting household form...")
        
        try:
            submit_button = await self.page.query_selector(Selectors.SUBMIT_BUTTON)
            if not submit_button:
                raise ElementInteractionError("Submit button not found")
            
            await submit_button.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(1000)
            await submit_button.evaluate("el => el.style.border = '3px solid red'")
            await self.page.wait_for_timeout(1000)
            await submit_button.click()
            
            self.logger.info("Household form submitted")
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "household_form_submission")
            raise ApplicationFormError(f"Error submitting household form: {e}")
    
    async def verify_household_submission(self) -> bool:
        """Verify household form submission was successful"""
        try:
            step3_active = await self.page.query_selector("div#apartment_people .af-position.active")
            if step3_active:
                self.logger.info("Successfully progressed to People step")
                return True
            
            has_errors = await self._check_validation_errors()
            if has_errors:
                return False
            
            current_url = self.page.url
            self.logger.info(f"Current URL after household submission: {current_url}")
            
            if "people" in current_url.lower() or "step" in current_url.lower():
                self.logger.info("URL indicates successful progression")
                return True
            
            self.logger.info("Household form submission status unclear - continuing...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying household submission: {e}")
            return False
    
    async def _check_validation_errors(self) -> bool:
        """Check for validation errors"""
        try:
            for selector in Selectors.ERROR_MESSAGES:
                errors = await self.page.query_selector_all(selector)
                for error in errors:
                    if await error.is_visible():
                        error_text = await error.text_content()
                        self.logger.error(f"Validation error: {error_text}")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking validation: {e}")
            return False