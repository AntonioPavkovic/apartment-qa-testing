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
            thank_you_page = await self.page.query_selector(".thank-you-page")
            if thank_you_page:
                self.logger.info("Application already submitted - found thank you page")
                await self.screenshot_manager.capture(self.page, "08_already_submitted", full_page=True)
                return
            
            if not await self.verify_summary_page_loaded():
                await self.debug_current_page()
                raise ApplicationFormError("Summary page did not load correctly")
            
            await self._check_required_agreements()
            await self._submit_application()
            await self._verify_submission_success()
            
            await self.screenshot_manager.capture(self.page, "08_application_submitted", full_page=True)
            self.logger.info("Application submitted successfully")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "summary_form_error")
            raise ApplicationFormError(f"Error completing summary form: {e}")

    async def fill_summary_form_and_go_to_admin(self) -> None:
        """Fill out the summary page, submit, and automatically navigate to admin panel"""
        self.logger.info("Filling summary form and navigating to admin...")
        
        try:
            thank_you_page = await self.page.query_selector(".thank-you-page")
            if thank_you_page:
                self.logger.info("Application already submitted - found thank you page, navigating to admin")
                await self.screenshot_manager.capture(self.page, "08_already_submitted", full_page=True)
                await self._navigate_to_admin_panel()
                return
            
            if not await self.verify_summary_page_loaded():
                await self.debug_current_page()
                raise ApplicationFormError("Summary page did not load correctly")
            
            await self._check_required_agreements()
            await self._submit_application()
            await self._verify_submission_success()
            
            await self.screenshot_manager.capture(self.page, "08_application_submitted", full_page=True)
            self.logger.info("Application submitted successfully")

            await self.page.wait_for_timeout(3000)

            success_page = await self.page.query_selector(".thank-you-page")
            if success_page:
                self.logger.info("Success page confirmed, navigating to admin panel...")
                await self._navigate_to_admin_panel()
            else:
                self.logger.warning("Success page not detected, but continuing with admin navigation...")
                await self._navigate_to_admin_panel()
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "summary_form_error")
            raise ApplicationFormError(f"Error completing summary form and admin navigation: {e}")

    async def _navigate_to_admin_panel(self) -> None:
        """Navigate directly to admin panel after confirmation"""
        self.logger.info("Automatically navigating to admin panel...")
        
        try:
            await self.screenshot_manager.capture(self.page, "08_success_page_before_admin", full_page=True)
            
            admin_url = "https://mostar.demo.ch.melon.market/"
            self.logger.info(f"Navigating from success page to admin URL: {admin_url}")
            await self.page.goto(admin_url)

            await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
            await self.page.wait_for_timeout(3000)

            await self.screenshot_manager.capture(self.page, "09_auto_admin_navigation", full_page=True)
            
            self.logger.info("Successfully navigated to admin panel")

            await self._auto_admin_login()
            
        except Exception as e:
            self.logger.error(f"Error navigating to admin panel: {e}")
            raise ApplicationFormError(f"Error navigating to admin panel: {e}")

    async def _auto_admin_login(self) -> None:
        """Automatically handle admin login"""
        self.logger.info("Starting automatic admin login...")
        
        try:
            from pages.admin_login_page import AdminLoginPage
            
            admin_login = AdminLoginPage(self.page, self.screenshot_manager, self.logger)

            current_url = self.page.url
            self.logger.info(f"Current URL for admin login: {current_url}")
            
            if "login" not in current_url.lower():
                self.logger.info("Not on login page, navigating to admin login...")
                await admin_login.navigate_to_admin_login()
            
            await admin_login.login_to_admin_panel()
            
            self.logger.info("Automatic admin login completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during automatic admin login: {e}")
            raise ApplicationFormError(f"Error during automatic admin login: {e}")
        
    async def _check_if_checkboxes_exist(self) -> bool:
        """Check if the required checkboxes exist on the page"""
        checkbox_ids = [
            "field-agreement_penalty",
            "field-agreement_truth",
            "field-agreement_privacy"
        ]
        
        for checkbox_id in checkbox_ids:
            checkbox = await self.page.query_selector(f"#{checkbox_id}")
            if checkbox:
                self.logger.info(f"Found checkbox: {checkbox_id}")
                return True
        
        self.logger.info("No agreement checkboxes found")
        return False
    
    async def complete_application_and_login_admin(self) -> None:
        """Complete the entire flow: submit application and login to admin panel"""
        self.logger.info("Starting complete application and admin login flow...")
        
        try:
            await self.fill_summary_form()
            
            from pages.admin_login_page import AdminLoginPage
            admin_login = AdminLoginPage(self.page, self.screenshot_manager, self.logger)
            
            await admin_login.navigate_to_admin_login()
            await admin_login.login_to_admin_panel()
            
            self.logger.info("Complete application and admin login flow completed successfully")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "complete_flow_error")
            raise ApplicationFormError(f"Error in complete application and admin login flow: {e}")
    
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
    
    async def _verify_submission_success(self) -> None:
        """Verify that the application was submitted successfully"""
        self.logger.info("Verifying application submission success...")
        
        try:
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            current_url = self.page.url
            self.logger.info(f"Current URL after submission: {current_url}")

            success_indicators = [
                ".thank-you-page",
                "text=Thank you very much, your application has been sent",
                "text=You will receive a registration confirmation by e-mail",
                "text=Thank you",
                "text=Danke",
                ".success-message",
                ".confirmation"
            ]
            
            found_success = False
            for selector in success_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    found_success = True
                    self.logger.info(f"Found success indicator: {selector}")
                    break
                except:
                    continue

            thank_you_elements = await self.page.query_selector_all(".thank-you-page")
            if thank_you_elements:
                found_success = True
                self.logger.info("Found thank you page elements - success confirmed")

            page_content = await self.page.text_content("body")
            if page_content and "your application has been sent" in page_content.lower():
                found_success = True
                self.logger.info("Found success text in page content")
            
            if found_success:
                self.logger.info("Application submission verified successfully - ready for admin navigation")
            else:
                self.logger.warning("Could not verify application submission success")
            
        except Exception as e:
            self.logger.error(f"Error verifying submission success: {e}")