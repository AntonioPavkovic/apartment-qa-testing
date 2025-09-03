from playwright.async_api import Page
from config.test_config import TestConfig
from exceptions.test_exceptions import ApplicationFormError
from utils.screenshot_manager import ScreenshotManager
from utils.logging import TestLogger

class SummaryFormPage:
    """Page Object Model for summary/final submission page functionality"""
    
    def __init__(self, page: Page, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.screenshot_manager = screenshot_manager
        self.logger = logger
    
    async def verify_summary_page_loaded(self) -> bool:
        """Verify that the summary page has loaded correctly"""
        self.logger.info("Verifying summary page...")
        
        try:
            await self.page.wait_for_selector("#apartment_agreement .af-position.active", timeout=TestConfig.DEFAULT_TIMEOUT)
            
            summary_indicators = [
                "#field-agreement_penalty",
                "#field-agreement_truth", 
                "#field-agreement_privacy",
                "h3:has-text('Summary')",
                ".section-info-label:has-text('Summary')"
            ]
            
            found_indicator = False
            for selector in summary_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    found_indicator = True
                    self.logger.info(f"Found summary page indicator: {selector}")
                    break
                except:
                    continue
            
            if found_indicator:
                self.logger.info("Summary page verified successfully")
                return True
            else:
                self.logger.error("No summary page indicators found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying summary page: {e}")
            return False
    
    async def debug_current_page(self) -> None:
        """Debug what's currently on the page"""
        self.logger.info("=== DEBUGGING CURRENT PAGE STATE ===")
        
        current_url = self.page.url
        self.logger.info(f"Current URL: {current_url}")

        title = await self.page.title()
        self.logger.info(f"Page title: {title}")

        steps = await self.page.query_selector_all(".af-steps")
        for i, step in enumerate(steps):
            class_list = await step.get_attribute("class")
            text = await step.text_content()
            self.logger.info(f"Step {i}: class='{class_list}', text='{text}'")
        
        sections = await self.page.query_selector_all(".section")
        self.logger.info(f"Found {len(sections)} sections on page")
        
        checkboxes = await self.page.query_selector_all("input[type='checkbox']")
        self.logger.info(f"Found {len(checkboxes)} checkboxes on page")
        for i, checkbox in enumerate(checkboxes[:5]):
            id_attr = await checkbox.get_attribute("id")
            self.logger.info(f"Checkbox {i}: id='{id_attr}'")
        
        await self.screenshot_manager.capture_error(self.page, "summary_page_debug")
    
    async def fill_summary_form(self) -> None:
        """Fill out the summary page checkboxes and submit"""
        self.logger.info("Filling summary form...")
        
        try:
            if not await self.verify_summary_page_loaded():
                await self.debug_current_page()
                raise ApplicationFormError("Summary page did not load correctly")
            
            await self._check_required_agreements()
            await self._submit_application()
            
            await self.screenshot_manager.capture(self.page, "08_application_submitted", full_page=True)
            self.logger.info("Application submitted successfully")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "summary_form_error")
            raise ApplicationFormError(f"Error completing summary form: {e}")
    
    async def _check_required_agreements(self) -> None:
        """Check all required agreement checkboxes"""
        self.logger.info("Checking required agreement checkboxes...")
        
        checkboxes = [
            ("field-agreement_penalty", "Compensation fee agreement"),
            ("field-agreement_truth", "Truthful answers confirmation"), 
            ("field-agreement_privacy", "Privacy policy agreement")
        ]
        
        for checkbox_id, description in checkboxes:
            try:
                checkbox = await self.page.query_selector(f"#{checkbox_id}")
                if checkbox:
                    is_checked = await checkbox.is_checked()
                    if not is_checked:
                        await checkbox.click()
                        self.logger.info(f"Checked: {description}")
                        await self.page.wait_for_timeout(300)
                    else:
                        self.logger.info(f"Already checked: {description}")
                else:
                    label = await self.page.query_selector(f"label[for='{checkbox_id}']")
                    if label:
                        await label.click()
                        self.logger.info(f"Checked via label: {description}")
                        await self.page.wait_for_timeout(300)
                    else:
                        self.logger.warning(f"Could not find checkbox: {checkbox_id}")
                        
            except Exception as e:
                self.logger.error(f"Error checking {description}: {e}")
                raise
    
    async def _submit_application(self) -> None:
        """Submit the final application"""
        self.logger.info("Submitting final application...")
        
        try:
            await self.page.wait_for_timeout(1000)
            
            submit_button = await self.page.query_selector("#application-btn-submit")
            if not submit_button:
                raise ApplicationFormError("Submit button not found")
            
            await submit_button.scroll_into_view_if_needed()
            await submit_button.click()
            self.logger.info("Clicked submit button")
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            self.logger.error(f"Error submitting application: {e}")
            raise