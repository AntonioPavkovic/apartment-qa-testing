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
            await self.page.wait_for_selector("#field-agreement_penalty", timeout=TestConfig.DEFAULT_TIMEOUT)
            await self.page.wait_for_selector("#application-btn-submit", timeout=TestConfig.DEFAULT_TIMEOUT)
            
            self.logger.info("Summary page verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying summary page: {e}")
            return False
    
    async def fill_summary_form(self) -> None:
        """Fill out the summary page checkboxes and submit"""
        self.logger.info("Filling summary form...")
        
        try:
            if not await self.verify_summary_page_loaded():
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
                    # Try clicking the label if checkbox not directly clickable
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
            # Wait for any validation to complete
            await self.page.wait_for_timeout(1000)
            
            submit_button = await self.page.query_selector("#application-btn-submit")
            if not submit_button:
                raise ApplicationFormError("Submit button not found")
            
            await submit_button.scroll_into_view_if_needed()
            await submit_button.click()
            self.logger.info("Clicked submit button")
            
            # Wait for submission to complete
            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            self.logger.error(f"Error submitting application: {e}")
            raise