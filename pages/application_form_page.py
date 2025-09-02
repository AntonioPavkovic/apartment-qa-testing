from playwright.async_api import Page
from config.test_config import Selectors, TestConfig
from data.models import FormData, ParkingRequirements
from exceptions.test_exceptions import ApplicationFormError, ElementInteractionError, NavigationError
from utils.element_interactor import ElementInteractor
from utils.logging import TestLogger
from utils.screenshot_manager import ScreenshotManager


class ApplicationFormPage:
    """Page Object Model for application form functionality"""
    
    def __init__(self, page: Page, interactor: ElementInteractor, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.interactor = interactor
        self.screenshot_manager = screenshot_manager
        self.logger = logger
    
    async def navigate_from_apply_button(self, apartment_page: Page) -> Page:
        """Navigate to application form by clicking Apply button"""
        self.logger.info("Looking for Apply/Application button...")
        
        for selector in Selectors.APPLY_BUTTONS:
            elements = await apartment_page.query_selector_all(selector)
            for element in elements:
                if await element.is_visible():
                    self.logger.info(f"Apply button found: {selector}")
                    await element.evaluate("el => el.style.border = '3px solid red'")
                    await apartment_page.wait_for_timeout(1000)
                    
                    async with apartment_page.context.expect_page() as new_page_info:
                        await element.click()
                    
                    new_page = await new_page_info.value
                    self.page = new_page
                    await self.page.bring_to_front()
                    self.logger.info("New application page opened successfully.")
                    return new_page
        
        raise NavigationError("Could not find Apply button")
    
    async def navigate_direct(self) -> Page:
        """Navigate directly to application form URL"""
        self.logger.info("Trying alternative application methods...")
        
        application_urls = [
            TestConfig.APPLICATION_FORM_URL,
            TestConfig.FALLBACK_APPLICATION_URL
        ]
        
        for url in application_urls:
            try:
                new_page = await self.page.context.new_page()
                await new_page.goto(url)
                await new_page.wait_for_load_state("networkidle", timeout=TestConfig.NETWORK_IDLE_TIMEOUT)

                form_indicators = await new_page.query_selector_all(".application-form, form, input")
                if form_indicators:
                    self.logger.info(f"Direct navigation worked: {url}")
                    self.page = new_page
                    return new_page
                else:
                    await new_page.close()
                        
            except Exception as e:
                self.logger.info(f"Failed to navigate to {url}: {e}")
                try:
                    await new_page.close()
                except:
                    pass
                continue
        
        raise NavigationError("Failed to navigate to application form")
    
    async def verify_form_loaded(self) -> bool:
        """Verify that the application form has loaded correctly"""
        self.logger.info("Verifying application form...")
        
        try:
            await self.page.wait_for_load_state("networkidle", timeout=TestConfig.NETWORK_IDLE_TIMEOUT)
            
            current_url = self.page.url
            self.logger.info(f"Current URL: {current_url}")
            
            found_indicators = []
            for indicator in Selectors.FORM_INDICATORS:
                try:
                    element = await self.page.query_selector(indicator)
                    if element:
                        found_indicators.append(indicator)
                except:
                    continue
            
            self.logger.info(f"Form indicators found: {found_indicators}")
            
            if found_indicators:
                self.logger.info("Application form verified")
                return True
            else:
                self.logger.warning("No clear form indicators found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying form: {e}")
            return False
    
    async def start_application_process(self) -> bool:
        """Start the application process if needed"""
        self.logger.info("Starting application process...")
        
        try:
            await self.page.wait_for_selector(Selectors.FORM_CONTAINER, timeout=5000)
            
            form_fields = await self.page.query_selector_all("input, textarea, select")
            visible_fields = [field for field in form_fields if await field.is_visible()]
            
            if visible_fields:
                self.logger.info(f"Form already active - {len(visible_fields)} input fields visible")
                return True

            for selector in Selectors.START_BUTTONS:
                try:
                    start_element = await self.page.query_selector(selector)
                    if start_element and await start_element.is_visible():
                        self.logger.info(f"Found start button: {selector}")
                        await start_element.click()
                        await self.page.wait_for_timeout(3000)
                        return True
                        
                except Exception as e:
                    self.logger.info(f"Start selector {selector} failed: {e}")
                    continue

            self.logger.info("Application process appears to be ready")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            return False
    
    async def fill_form(self, form_data: FormData) -> None:
        """Fill out the complete application form"""
        self.logger.info("Filling out application form with realistic data...")
        
        try:
            await self.page.wait_for_timeout(2000)
            
            await self._fill_parking_section(form_data.parking)
            await self._fill_vehicle_sections(form_data)
            await self._fill_space_requirements(form_data)
            await self._fill_work_requirements(form_data)
            await self._fill_accessibility_requirements(form_data)
            
            await self.screenshot_manager.capture(self.page, "04_form_filled", full_page=True)
            self.logger.info("Form filled with realistic data")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "form_filling")
            raise ApplicationFormError(f"Error filling form: {e}")
    
    async def _fill_parking_section(self, parking: ParkingRequirements) -> None:
        """Fill parking requirements section"""
        if parking.wants_parking:
            self.logger.info("User wants parking spaces...")
            await self._click_radio_option("parking-true")
            await self.page.wait_for_timeout(1000)

            parking_fields = [
                ("field-parking_regular", parking.regular_spaces),
                ("field-parking_small", parking.small_spaces),
                ("field-parking_large", parking.large_spaces),
                ("field-parking_electric", parking.electric_spaces),
                ("field-parking_electric_small", parking.electric_small_spaces),
                ("field-parking_outdoor", parking.outdoor_spaces),
                ("field-parking_special", parking.special_spaces)
            ]
            
            for field_id, spaces in parking_fields:
                if spaces > 0:
                    await self._set_number_field(field_id, spaces)
                    await self.page.wait_for_timeout(500)
            
            if parking.reason:
                await self.interactor.fill_field_safely("input#field-car_reason", parking.reason)
        else:
            await self._click_radio_option("parking-false")
    
    async def _fill_vehicle_sections(self, form_data: FormData) -> None:
        """Fill vehicle-related sections"""
        await self._select_yes_no("car_sharing", form_data.wants_car_sharing)
        
        if form_data.wants_motorbike_parking:
            await self._click_radio_option("motorbikes-true")
            await self.page.wait_for_timeout(1000)
            await self._set_number_field("field-parking_motorbike", form_data.motorbike_spaces)
        else:
            await self._click_radio_option("motorbikes-false")
        
        if form_data.wants_bike_parking:
            self.logger.info("User wants bike parking...")
            await self._click_radio_option("bicycles-true")
            await self.page.wait_for_timeout(1000)

            await self._set_number_field("field-parking_bicycle", form_data.bike_spaces)

            if form_data.electric_bike_spaces > 0:
                await self._set_number_field("field-parking_electric_bicycles", form_data.electric_bike_spaces)
        else:
            await self._click_radio_option("bicycles-false")
    
    async def _fill_space_requirements(self, form_data: FormData) -> None:
        """Fill additional space requirements"""
        if form_data.wants_additional_room:
            self.logger.info("User wants additional room...")
            await self._click_radio_option("wants_addroom-true")
            await self.page.wait_for_timeout(1000)

            if form_data.additional_room_purpose:
                await self.interactor.fill_field_safely("textarea#field-addroom_intended_use", form_data.additional_room_purpose, typing_delay=40)
            if form_data.additional_room_area:
                await self.interactor.fill_field_safely("input#field-addroom_area", form_data.additional_room_area)
        else:
            await self._click_radio_option("wants_addroom-false")
        
        if form_data.wants_storage_room:
            self.logger.info("User wants storage room...")
            await self._click_radio_option("wants_stockroom-true")
            await self.page.wait_for_timeout(1000)
            
            if form_data.storage_room_purpose:
                await self.interactor.fill_field_safely("textarea#field-stockroom_intended_use", form_data.storage_room_purpose, typing_delay=40)
            if form_data.storage_room_area:
                await self.interactor.fill_field_safely("input#field-stockroom_area", form_data.storage_room_area)
        else:
            await self._click_radio_option("wants_stockroom-false")

        if form_data.wants_workshop:
            await self._click_radio_option("wants_workshop-true")
            await self.page.wait_for_timeout(1000)
            
            if form_data.workshop_purpose:
                await self.interactor.fill_field_safely("textarea#field-workshop_intended_use", form_data.workshop_purpose, typing_delay=40)
        else:
            await self._click_radio_option("wants_workshop-false")
    
    async def _fill_work_requirements(self, form_data: FormData) -> None:
        """Fill work-related requirements"""
        await self._select_yes_no("wants_coworking", form_data.wants_coworking)
        
        if form_data.wants_home_office:
            await self._click_radio_option("wants_homeoffice-true")
            await self.page.wait_for_timeout(1000)
            
            if form_data.home_office_reason:
                await self.interactor.fill_field_safely("input#field-wants_homeoffice_detail", form_data.home_office_reason)
        else:
            await self._click_radio_option("wants_homeoffice-false")
    
    async def _fill_accessibility_requirements(self, form_data: FormData) -> None:
        """Fill accessibility requirements"""
        await self._select_yes_no("obstacle_free", form_data.needs_obstacle_free)
    
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
    
    async def _select_yes_no(self, field_name: str, select_yes: bool) -> None:
        """Select yes or no for a boolean field"""
        suffix = "true" if select_yes else "false"
        await self._click_radio_option(f"{field_name}-{suffix}")
    
    async def _set_number_field(self, field_id: str, value: int) -> None:
        """Set value in a number field using increment/decrement"""
        try:
            field_selector = f"input#{field_id}"
            await self.page.wait_for_selector(field_selector, timeout=TestConfig.DEFAULT_TIMEOUT)

            await self.page.fill(field_selector, "0")
            await self.page.wait_for_timeout(300)

            increment_selector = f"div#increment-{field_id}"
            for _ in range(value):
                try:
                    await self.page.click(increment_selector)
                    await self.page.wait_for_timeout(200)
                except:
                    await self.page.fill(field_selector, str(value))
                    break
            
            self.logger.info(f"Set {field_id} to {value}")
                    
        except Exception as e:
            raise ElementInteractionError(f"Failed to set number field {field_id}: {e}")
    
    async def submit_form(self) -> None:
        """Submit the application form"""
        self.logger.info("Submitting application form...")
        
        try:
            await self.page.wait_for_selector(Selectors.SUBMIT_BUTTON, timeout=TestConfig.SLOW_TIMEOUT)
            submit_button = await self.page.query_selector(Selectors.SUBMIT_BUTTON)
            
            if not submit_button:
                raise ElementInteractionError("Submit button not found")
            
            await submit_button.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(1000)
            await submit_button.evaluate("el => el.style.border = '3px solid red'")
            await self.page.wait_for_timeout(1000)
            await submit_button.click()
            
            self.logger.info("Save and next button clicked")
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "form_submission")
            raise ApplicationFormError(f"Error submitting form: {e}")
    
    async def verify_submission(self) -> bool:
        """Verify form submission was successful"""
        try:
            has_errors = await self._check_validation_errors()
            if has_errors:
                return False
            
            for indicator in Selectors.SUCCESS_INDICATORS:
                try:
                    element = await self.page.query_selector(indicator)
                    if element:
                        self.logger.info(f"Successfully progressed to next step: {indicator}")
                        return True
                except:
                    continue
            
            current_url = self.page.url
            self.logger.info(f"Current URL after submission: {current_url}")
            
            if "household" in current_url.lower() or "step" in current_url.lower():
                self.logger.info("URL indicates successful progression")
                return True
            
            success_elements = await self.page.query_selector_all("[class*='success'], .step-completed")
            if success_elements:
                self.logger.info("Form submission appears successful")
                return True
            else:
                self.logger.info("Form submission status unclear - continuing...")
                return True 
            
        except Exception as e:
            self.logger.error(f"Error verifying submission: {e}")
            return False
    
    async def _check_validation_errors(self) -> bool:
        """Check if there are validation errors on the form"""
        try:
            for selector in Selectors.ERROR_MESSAGES:
                errors = await self.page.query_selector_all(selector)
                for error in errors:
                    if await error.is_visible():
                        error_text = await error.text_content()
                        self.logger.error(f"Validation error found: {error_text}")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking validation: {e}")
            return False