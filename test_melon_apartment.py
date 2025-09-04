import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser

from config.test_config import TestConfig
from data.factories import TestDataFactory
from data.models import ApartmentDetails, TestResult
from exceptions.test_exceptions import ApplicationFormError, NavigationError
from pages.apartment_listing_page import ApartmentListingPage
from pages.application_form_page import ApplicationFormPage
from pages.components.wishlist import WishlistComponent
from pages.people_form_page import PeopleFormPage
from pages.summary_form_page import SummaryFormPage
from pages.admin_login_page import AdminLoginPage
from utils.element_interactor import ElementInteractor
from utils.logging import TestLogger
from utils.screenshot_manager import ScreenshotManager
from pages.household_form_page import HouseholdFormPage

class TestCompleteApartmentWorkflow:
    """Main test class orchestrating the complete apartment application workflow"""
    
    def __init__(self):
        self.logger = TestLogger("TestCompleteApartmentWorkflow")
        self.screenshot_manager = ScreenshotManager()
    
    @pytest.fixture(scope="session")
    async def browser_setup(self):
        """Set up browser for test session"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=TestConfig.BROWSER_HEADLESS, 
                slow_mo=TestConfig.BROWSER_SLOW_MO
            )
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def page(self, browser_setup: Browser):
        """Provide fresh page for each test"""
        context = await browser_setup.new_context()
        page = await context.new_page()
        yield page
        await context.close()
    
    async def test_complete_apartment_workflow(self, page: Page):
        """Complete workflow from browsing apartments to submitting application"""
        start_time = time.time()
        result = TestResult(success=False)
        
        try:
            async with self.logger.log_phase("COMPLETE APARTMENT WORKFLOW TEST"):
                apartment_details = await self._execute_apartment_browsing_phase(page)
                result.apartment_details = apartment_details
                
                application_page = await self._execute_application_navigation_phase(page)
                
                await self._execute_form_completion_phase(application_page)
                
                await self._execute_admin_verification_phase(page)
                
                result.success = True
                result.execution_time = time.time() - start_time
                
                print("\n COMPLETE APARTMENT WORKFLOW COMPLETED SUCCESSFULLY!")
                
        except Exception as e:
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            
            error_screenshot = await self.screenshot_manager.capture_error(page, "workflow")
            result.screenshot_paths.append(error_screenshot)
            
            print(f"\n Test failed with exception: {e}")
            raise
    
    async def test_complete_apartment_workflow_without_admin(self, page: Page):
        """Complete workflow without admin verification (original functionality)"""
        start_time = time.time()
        result = TestResult(success=False)
        
        try:
            async with self.logger.log_phase("COMPLETE APARTMENT WORKFLOW TEST (WITHOUT ADMIN)"):
                apartment_details = await self._execute_apartment_browsing_phase(page)
                result.apartment_details = apartment_details
                
                application_page = await self._execute_application_navigation_phase(page)
                
                await self._execute_form_completion_phase(application_page)
                
                result.success = True
                result.execution_time = time.time() - start_time
                
                print("\n COMPLETE APARTMENT WORKFLOW COMPLETED SUCCESSFULLY!")
                
        except Exception as e:
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            
            error_screenshot = await self.screenshot_manager.capture_error(page, "workflow")
            result.screenshot_paths.append(error_screenshot)
            
            print(f"\n Test failed with exception: {e}")
            raise
    
    async def test_admin_login_only(self, page: Page):
        """Test only the admin login functionality"""
        try:
            async with self.logger.log_phase("ADMIN LOGIN ONLY TEST"):
                admin_login_page = AdminLoginPage(page, self.screenshot_manager, self.logger)
                
                await admin_login_page.navigate_to_admin_login()
                await admin_login_page.login_to_admin_panel()
                
                self.logger.info("Admin login test completed successfully")
                print("\n ADMIN LOGIN TEST COMPLETED SUCCESSFULLY!")
                
        except Exception as e:
            self.logger.error(f"Admin login test failed: {e}")
            await self.screenshot_manager.capture_error(page, "admin_login_test_failure")
            print(f"\n Admin login test failed: {e}")
            raise
    
    async def _execute_apartment_browsing_phase(self, page: Page) -> ApartmentDetails:
        """Execute apartment browsing and selection phase"""
        async with self.logger.log_phase("PHASE 1: Apartment Browsing and Selection"):
            interactor = ElementInteractor(page, self.logger)
            listing_page = ApartmentListingPage(page, interactor, self.screenshot_manager, self.logger)
            wishlist = WishlistComponent(page, interactor, self.screenshot_manager, self.logger)
            
            await listing_page.navigate()
            apartments = await listing_page.find_available_apartments()
            
            selected_apartment = await listing_page.select_random_apartment(apartments)
            apartment_details = await listing_page.extract_apartment_details(selected_apartment)
            
            wishlist_success = await wishlist.add_apartment(selected_apartment)
            if wishlist_success:
                await wishlist.verify_wishlist_panel()
            
            return apartment_details
    
    async def _execute_application_navigation_phase(self, page: Page) -> Page:
        """Execute navigation to application form"""
        async with self.logger.log_phase("PHASE 2: Application Form Navigation"):
            interactor = ElementInteractor(page, self.logger)
            form_page = ApplicationFormPage(page, interactor, self.screenshot_manager, self.logger)
            
            try:
                application_page = await form_page.navigate_from_apply_button(page)
            except NavigationError:
                self.logger.warning("Could not find Apply button, trying alternative methods...")
                application_page = await form_page.navigate_direct()
            
            if not await form_page.verify_form_loaded():
                await self.screenshot_manager.capture_error(application_page, "no_application")
                raise NavigationError("Failed to navigate to application form")
            
            return application_page
    
    async def _execute_form_completion_phase(self, page: Page) -> None:
        """Execute form filling and submission for all steps"""
        
        async with self.logger.log_phase("PHASE 3A: Object Form Completion"):
            interactor = ElementInteractor(page, self.logger)
            form_page = ApplicationFormPage(page, interactor, self.screenshot_manager, self.logger)
            
            await form_page.start_application_process()
            form_data = TestDataFactory.create_realistic_applicant()
            await form_page.fill_form(form_data)
            await form_page.submit_form()
            
            success = await form_page.verify_submission()
            if not success:
                raise ApplicationFormError("Object form submission verification failed")
            
            await self.screenshot_manager.capture(page, "05_object_form_submitted", full_page=True)
            self.logger.info("Object form submitted successfully")
        
        async with self.logger.log_phase("PHASE 3B: Household Form Completion"):
            interactor = ElementInteractor(page, self.logger)
            household_page = HouseholdFormPage(page, interactor, self.screenshot_manager, self.logger)
            
            if not await household_page.verify_household_form_loaded():
                raise ApplicationFormError("Household form did not load correctly")

            await household_page.fill_household_form(form_data.household)
            await household_page.submit_household_form()
            
            success = await household_page.verify_household_submission()
            if not success:
                raise ApplicationFormError("Household form submission verification failed")
            
            await self.screenshot_manager.capture(page, "06_household_form_submitted", full_page=True)
            self.logger.info("Household form submitted successfully")
        
        async with self.logger.log_phase("PHASE 3C: People Form Completion"):
            interactor = ElementInteractor(page, self.logger)
            people_page = PeopleFormPage(page, interactor, self.screenshot_manager, self.logger)

            family_data = TestDataFactory.create_family_with_child_data()
            await people_page.fill_people_form(family_data)

            await self.screenshot_manager.capture(page, "07_people_form_submitted", full_page=True)
            self.logger.info("People form submitted successfully")

        async with self.logger.log_phase("PHASE 3D: Summary Form Completion"):
            summary_page = SummaryFormPage(page, self.screenshot_manager, self.logger)
            
            await summary_page.fill_summary_form()
            
            self.logger.info("Summary form and final application submitted successfully")
    
    async def _execute_admin_verification_phase(self, page: Page) -> None:
        """Execute admin login and application verification phase"""
        async with self.logger.log_phase("PHASE 4: Admin Panel Verification"):
            
            context = page.context
            all_pages = context.pages
            self.logger.info(f"Found {len(all_pages)} open pages/tabs")
            
            admin_page = None
            
            for p in all_pages:
                url = p.url
                if "mostar.demo.ch.melon.market" in url and "login" in url:
                    admin_page = p
                    self.logger.info(f"Found existing admin tab: {url}")
                    break
            
            if not admin_page:
                admin_page = page
            
            admin_login_page = AdminLoginPage(admin_page, self.screenshot_manager, self.logger)

            await admin_login_page.navigate_to_admin_login()
            await admin_login_page.login_to_admin_panel()
            
            await self.screenshot_manager.capture(admin_page, "09_admin_verification_complete", full_page=True)
            self.logger.info("Admin verification phase completed successfully")

@pytest.mark.asyncio
async def test_complete_workflow_with_admin():
    """Pytest function for complete workflow with admin verification"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=TestConfig.BROWSER_HEADLESS, 
            slow_mo=TestConfig.BROWSER_SLOW_MO
        )
        page = await browser.new_page()
        
        test_suite = TestCompleteApartmentWorkflow()
        
        try:
            await test_suite.test_complete_apartment_workflow(page)
        finally:
            await browser.close()

@pytest.mark.asyncio
async def test_complete_workflow_without_admin():
    """Pytest function for complete workflow without admin verification"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=TestConfig.BROWSER_HEADLESS, 
            slow_mo=TestConfig.BROWSER_SLOW_MO
        )
        page = await browser.new_page()
        
        test_suite = TestCompleteApartmentWorkflow()
        
        try:
            await test_suite.test_complete_apartment_workflow_without_admin(page)
        finally:
            await browser.close()

@pytest.mark.asyncio
async def test_admin_login_standalone():
    """Pytest function for testing admin login only"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=TestConfig.BROWSER_HEADLESS, 
            slow_mo=TestConfig.BROWSER_SLOW_MO
        )
        page = await browser.new_page()
        
        test_suite = TestCompleteApartmentWorkflow()
        
        try:
            await test_suite.test_admin_login_only(page)
        finally:
            await browser.close()

if __name__ == "__main__":
    async def run_complete_workflow_test():
        """Main execution function for running tests independently"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=TestConfig.BROWSER_HEADLESS, 
                slow_mo=TestConfig.BROWSER_SLOW_MO
            )
            page = await browser.new_page()
            
            test_suite = TestCompleteApartmentWorkflow()
            
            try:
                print("=== STARTING COMPLETE APARTMENT WORKFLOW TEST WITH ADMIN VERIFICATION ===")
                await test_suite.test_complete_apartment_workflow(page)
                
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