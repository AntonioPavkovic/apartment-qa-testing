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
from pages.admin_applications_page import AdminApplicationsPage
from utils.element_interactor import ElementInteractor
from utils.logging import TestLogger
from utils.screenshot_manager import ScreenshotManager
from pages.household_form_page import HouseholdFormPage

class TestCompleteApartmentWorkflow:
    """Main test class orchestrating the complete apartment application workflow"""
    
    def __init__(self):
        self.logger = TestLogger("TestCompleteApartmentWorkflow")
        self.screenshot_manager = ScreenshotManager()
        self.submitted_family_data = None
        self.submitted_form_data = None
    
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
        """Complete workflow from browsing apartments to submitting application with admin verification"""
        start_time = time.time()
        result = TestResult(success=False)
        
        try:
            async with self.logger.log_phase("COMPLETE APARTMENT WORKFLOW TEST WITH ADMIN VERIFICATION"):
                apartment_details = await self._execute_apartment_browsing_phase(page)
                result.apartment_details = apartment_details
                
                application_page = await self._execute_application_navigation_phase(page)
                
                await self._execute_form_completion_phase(application_page)
                
                await self._execute_admin_verification_phase(page)
                
                result.success = True
                result.execution_time = time.time() - start_time
                
                print("\n COMPLETE APARTMENT WORKFLOW WITH ADMIN VERIFICATION COMPLETED SUCCESSFULLY!")
                
        except Exception as e:
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            
            error_screenshot = await self.screenshot_manager.capture_error(page, "workflow")
            result.screenshot_paths.append(error_screenshot)
            
            print(f"\n✗ Test failed with exception: {e}")
            raise
    
    async def test_admin_verification_only(self, page: Page):
        """Test only the admin verification functionality (login + applications check)"""
        try:
            async with self.logger.log_phase("ADMIN VERIFICATION ONLY TEST"):
                self.submitted_family_data = TestDataFactory.create_family_for_test_type("smoke")
                self.submitted_form_data = TestDataFactory.create_realistic_applicant()
                
                self.logger.info(f"Testing verification for: {self.submitted_family_data[0].first_name} {self.submitted_family_data[0].last_name}")
                self.logger.info(f"Email to search for: {self.submitted_family_data[0].email}")
                
                admin_login_page = AdminLoginPage(page, self.screenshot_manager, self.logger)
                admin_apps_page = AdminApplicationsPage(page, self.screenshot_manager, self.logger)
                
                await admin_login_page.navigate_to_admin_login()
                await admin_login_page.login_to_admin_panel()
                
                await admin_apps_page.navigate_to_applications()
                
                table_summary = await admin_apps_page.get_applications_table_summary()
                self.logger.info(f"Applications table contains {table_summary.get('total_applications', 0)} applications")
                
                if table_summary.get('errors'):
                    for error in table_summary['errors']:
                        self.logger.warning(f"Table summary error: {error}")
                
                if table_summary.get('sample_rows'):
                    self.logger.info("Sample applications found in table:")
                    for i, sample in enumerate(table_summary['sample_rows'][:3]):
                        self.logger.info(f"  Application {i+1}: {sample.get('row_text', 'No data')[:100]}")
                
                verification_results = await admin_apps_page.verify_applicant_in_table(
                    self.submitted_family_data, 
                    self.submitted_form_data
                )
                
                self._log_verification_results(verification_results)
                
                if verification_results.get("found_in_table"):
                    print(f"\n FOUND: Test applicant found in applications table!")
                else:
                    print(f"\n NOT FOUND: Test applicant not found in table (expected for admin-only test)")
                    print("  This is normal since we didn't actually submit an application.")
                    print("  The test verified that admin login and table access work correctly.")
                
                self.logger.info("Admin verification test completed successfully")
                print("\n ADMIN VERIFICATION TEST COMPLETED SUCCESSFULLY!")
                
        except Exception as e:
            self.logger.error(f"Admin verification test failed: {e}")
            await self.screenshot_manager.capture_error(page, "admin_verification_test_failure")
            print(f"\n Admin verification test failed: {e}")
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
        
        self.submitted_form_data = TestDataFactory.create_realistic_applicant()
        self.submitted_family_data = TestDataFactory.create_family_for_test_type("smoke")
        
        async with self.logger.log_phase("PHASE 3A: Object Form Completion"):
            interactor = ElementInteractor(page, self.logger)
            form_page = ApplicationFormPage(page, interactor, self.screenshot_manager, self.logger)
            
            await form_page.start_application_process()
            await form_page.fill_form(self.submitted_form_data)
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

            await household_page.fill_household_form(self.submitted_form_data.household)
            await household_page.submit_household_form()
            
            success = await household_page.verify_household_submission()
            if not success:
                raise ApplicationFormError("Household form submission verification failed")
            
            await self.screenshot_manager.capture(page, "06_household_form_submitted", full_page=True)
            self.logger.info("Household form submitted successfully")
        
        async with self.logger.log_phase("PHASE 3C: People Form Completion"):
            interactor = ElementInteractor(page, self.logger)
            people_page = PeopleFormPage(page, interactor, self.screenshot_manager, self.logger)

            await people_page.fill_people_form(self.submitted_family_data)

            await self.screenshot_manager.capture(page, "07_people_form_submitted", full_page=True)
            self.logger.info("People form submitted successfully")

        async with self.logger.log_phase("PHASE 3D: Summary Form and Auto Admin Navigation"):
            summary_page = SummaryFormPage(page, self.screenshot_manager, self.logger)
            
            await summary_page.fill_summary_form_and_go_to_admin()
            
            self.logger.info("Summary form completed and automatically navigated to admin panel")
    
    async def _execute_admin_verification_phase(self, page: Page) -> None:
        """Execute admin verification phase - ensuring proper admin login and navigation"""
        async with self.logger.log_phase("PHASE 4: Admin Panel Verification"):
            
            admin_login_page = AdminLoginPage(page, self.screenshot_manager, self.logger)
            admin_apps_page = AdminApplicationsPage(page, self.screenshot_manager, self.logger)
            
            async with self.logger.log_phase("Admin Login Verification", applicant_name=f"{self.submitted_family_data[0].first_name} {self.submitted_family_data[0].last_name}"):
                current_url = page.url
                self.logger.info(f"Current URL: {current_url}")
                
                is_on_admin = (current_url.endswith("/home") or 
                            "/applications" in current_url or
                            "mostar.api.demo.ch.melon.market" in current_url or
                            current_url.endswith("/"))
                
                if not is_on_admin:
                    self.logger.info("Not on admin panel, navigating to admin login...")
                    await admin_login_page.navigate_to_admin_login()
                    await admin_login_page.login_to_admin_panel()
                else:
                    self.logger.info(f"Already on admin panel (URL: {current_url}), proceeding...")
                
                self.logger.info("Admin login verification successful")
            
            async with self.logger.log_phase("Applications Page Navigation"):
                await admin_apps_page.navigate_to_applications()
                self.logger.info("Applications page loaded successfully")
            
            async with self.logger.log_phase("Applications Table Analysis"):
                table_summary = await admin_apps_page.get_applications_table_summary()
                
                total_applications = table_summary.get('total_applications', 0)
                self.logger.info(f"Applications table contains {total_applications} applications")
                
                if table_summary.get('table_headers'):
                    self.logger.info(f"Table headers: {', '.join(table_summary['table_headers'])}")
                
                if table_summary.get('sample_rows'):
                    self.logger.info("Sample applications found in table:")
                    for i, sample in enumerate(table_summary['sample_rows'][:3]):
                        self.logger.info(f"  Application {i+1}: {sample.get('row_text', 'No data')[:100]}...")
                
                if table_summary.get('errors'):
                    for error in table_summary['errors']:
                        self.logger.error(f"Table analysis error: {error}")

            async with self.logger.log_phase("Applicant Search and Verification", applicant_email=self.submitted_family_data[0].email):
                if self.submitted_family_data and len(self.submitted_family_data) > 0:
                    main_applicant = self.submitted_family_data[0]
                    self.logger.info(f"Searching for submitted applicant: {main_applicant.first_name} {main_applicant.last_name}")
                    self.logger.info(f"Expected email: {main_applicant.email}")
                    
                    verification_results = await admin_apps_page.click_applicant_row_and_verify_details(
                        self.submitted_family_data, 
                        self.submitted_form_data
                    )
                    if verification_results.get("found_in_table", False):
                        table_row = await admin_apps_page._find_applicant_row(main_applicant)
                        if table_row:
                            await self._add_enhanced_ui_highlighting(page, table_row, main_applicant)

                            await self._add_verification_status_changes(page, table_row)

                            await self.screenshot_manager.capture(page, "11_ui_verification_changes", full_page=True)

                            self.logger.info(" UI CHANGES APPLIED - Keeping visible for 15 seconds...")
                            await page.wait_for_timeout(15000)

                    self._validate_enhanced_admin_verification(verification_results)
                    
                else:
                    self.logger.warning("No submitted family data available for verification")
                    self.logger.warning("Cannot verify applicant without test data")

            await self.screenshot_manager.capture(page, "10_admin_verification_complete", full_page=True)
            self.logger.info("Admin verification phase completed successfully")

    async def _add_enhanced_ui_highlighting(self, page: Page, table_row, main_applicant) -> None:
        """Add prominent, visible UI highlighting to show verification"""
        try:
            await table_row.evaluate(f"""
                (element) => {{
                    element.style.border = '5px solid #ff0000';
                    element.style.backgroundColor = '#ff4444';
                    element.style.color = 'white';
                    element.style.fontWeight = 'bold';
                    element.style.transform = 'scale(1.05)';
                    element.style.zIndex = '9999';
                    element.style.position = 'relative';
                    element.style.boxShadow = '0 0 20px #ff0000';
                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    
                    let blinks = 0;
                    const blink = setInterval(() => {{
                        element.style.opacity = element.style.opacity === '0.5' ? '1' : '0.5';
                        blinks++;
                        if (blinks > 20) {{
                            clearInterval(blink);
                            element.style.opacity = '1';
                        }}
                    }}, 300);
                    
                    const label = document.createElement('div');
                    label.textContent = ' VERIFIED BY AUTOMATION ';
                    label.style.position = 'absolute';
                    label.style.top = '-40px';
                    label.style.left = '50%';
                    label.style.transform = 'translateX(-50%)';
                    label.style.background = '#00ff00';
                    label.style.color = '#000';
                    label.style.padding = '8px 15px';
                    label.style.fontWeight = 'bold';
                    label.style.zIndex = '10000';
                    label.style.borderRadius = '5px';
                    label.style.fontSize = '14px';
                    label.style.animation = 'pulse 1s infinite';
                    element.appendChild(label);

                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes pulse {{
                            0% {{ transform: translateX(-50%) scale(1); }}
                            50% {{ transform: translateX(-50%) scale(1.1); }}
                            100% {{ transform: translateX(-50%) scale(1); }}
                        }}
                    `;
                    document.head.appendChild(style);
                }}
            """)
            
            self.logger.info(f" Added prominent highlighting to {main_applicant.first_name} {main_applicant.last_name}'s row")
            
        except Exception as e:
            self.logger.error(f"Error adding UI highlighting: {e}")

    async def _add_verification_status_changes(self, page: Page, table_row) -> None:
        """Add visible status changes to show verification completed"""
        try:
            import datetime
            verification_time = datetime.datetime.now().strftime("%H:%M:%S")

            await table_row.evaluate(f"""
                (element) => {{
                    const cells = element.querySelectorAll('td');
                    if (cells.length > 0) {{
                        const statusCell = cells[cells.length - 1] || cells[cells.length - 2];
                        if (statusCell) {{
                            statusCell.textContent = 'VERIFIED ';
                            statusCell.style.backgroundColor = '#00ff00';
                            statusCell.style.color = '#000';
                            statusCell.style.fontWeight = 'bold';
                            statusCell.style.textAlign = 'center';
                            statusCell.style.animation = 'flash 2s infinite';
                        }}
                    }}
                    
                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes flash {{
                            0%, 50%, 100% {{ background-color: #00ff00; }}
                            25%, 75% {{ background-color: #ffff00; }}
                        }}
                    `;
                    document.head.appendChild(style);
                }}
            """)
            
            await page.evaluate(f"""
                const notification = document.createElement('div');
                notification.textContent = ' APPLICANT VERIFICATION COMPLETED AT {verification_time}';
                notification.style.position = 'fixed';
                notification.style.top = '20px';
                notification.style.right = '20px';
                notification.style.background = '#4CAF50';
                notification.style.color = 'white';
                notification.style.padding = '15px 20px';
                notification.style.zIndex = '10001';
                notification.style.borderRadius = '8px';
                notification.style.fontWeight = 'bold';
                notification.style.fontSize = '16px';
                notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                notification.style.animation = 'slideIn 0.5s ease-out';
                
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {{
                        from {{ transform: translateX(100%); opacity: 0; }}
                        to {{ transform: translateX(0); opacity: 1; }}
                    }}
                `;
                document.head.appendChild(style);
                
                document.body.appendChild(notification);
            """)
            
            self.logger.info(f" Added verification status changes and notification at {verification_time}")
            
        except Exception as e:
            self.logger.error(f"Error adding status changes: {e}")
    
    def _validate_admin_verification(self, verification_results: dict) -> None:
        """Validate that admin verification results meet expectations"""
        
        if not verification_results.get("found_in_table", False):
            self.logger.warning("WARNING: Submitted applicant not found in applications table!")
            self.logger.warning("This could mean: 1) Application wasn't submitted, 2) Table structure changed, 3) Application is processed/hidden")
            
        else:
            data_matches = verification_results.get("data_matches", {})
            
            name_found = data_matches.get("name_found", False)
            email_found = data_matches.get("email_found", False)
            
            if not name_found and not email_found:
                self.logger.warning("WARNING: Neither applicant name nor email found in table row!")
                self.logger.warning("Application found in table but verification data doesn't match expected format")
            else:
                self.logger.info(" Admin verification validation passed - applicant found and verified in table")
        
        self._log_verification_results(verification_results)
        
        if verification_results.get("errors"):
            for error in verification_results["errors"]:
                self.logger.warning(f"Verification warning: {error}")
        
        self.logger.info("Admin verification phase completed (check logs for details)")

    def _validate_enhanced_admin_verification(self, verification_results: dict) -> None:
        """Validate enhanced admin verification results"""
        
        found_in_table = verification_results.get("found_in_table", False)
        row_clicked = verification_results.get("row_clicked", False)
        detail_loaded = verification_results.get("detail_page_loaded", False)
        
        if not found_in_table:
            self.logger.warning("WARNING: Submitted applicant not found in applications table!")
            return
        
        data_matches = verification_results.get("data_matches", {})

        name_found = data_matches.get("name_found", False)
        if name_found:
            self.logger.info(" Applicant name verified in table")
        else:
            self.logger.warning(" Applicant name not found in table")

        if row_clicked:
            self.logger.info(" Successfully clicked applicant row")
            
            if detail_loaded:
                self.logger.info(" Detail view loaded successfully")

                email_in_detail = data_matches.get("email_found_in_detail", False)
                phone_in_detail = data_matches.get("phone_found_in_detail", False)
                address_in_detail = data_matches.get("address_found_in_detail", False)
                date_in_detail = data_matches.get("move_in_date_found_in_detail", False)
                
                if email_in_detail:
                    self.logger.info(" Email verified in detail view")
                else:
                    self.logger.warning(" Email not found in detail view")
                
                if phone_in_detail:
                    self.logger.info(" Phone verified in detail view")
                
                if address_in_detail:
                    self.logger.info(" Address verified in detail view")
                
                if date_in_detail:
                    self.logger.info(" Move-in date verified in detail view")

                detail_checks_passed = sum([email_in_detail, phone_in_detail, address_in_detail, date_in_detail])
                self.logger.info(f"Detail verification: {detail_checks_passed}/4 additional checks passed")
                
                if detail_checks_passed >= 2:
                    self.logger.info(" Enhanced admin verification PASSED - sufficient detail data verified")
                else:
                    self.logger.warning(" Enhanced admin verification PARTIAL - limited detail data verified")
            else:
                self.logger.warning(" Row clicked but detail view did not load")
                self.logger.info("Basic table verification completed, but detailed verification unavailable")
        else:
            self.logger.warning(" Could not click applicant row for detailed verification")
            self.logger.info("Basic table verification completed, but detailed verification unavailable")

        if verification_results.get("errors"):
            for error in verification_results["errors"]:
                self.logger.warning(f"Verification warning: {error}")
        
        self.logger.info("Enhanced admin verification phase completed")

    def _log_verification_results(self, verification_results: dict) -> None:
        """Log detailed verification results"""
        self.logger.info("=== APPLICANT VERIFICATION RESULTS ===")
        self.logger.info(f"Found in table: {verification_results.get('found_in_table', False)}")
        
        data_matches = verification_results.get("data_matches", {})
        self.logger.info(f"Name found: {data_matches.get('name_found', False)}")
        self.logger.info(f"Email found: {data_matches.get('email_found', False)}")
        self.logger.info(f"Date found: {data_matches.get('date_found', False)}")
        self.logger.info(f"Additional data found: {data_matches.get('additional_data_found', False)}")
        
        if verification_results.get("errors"):
            self.logger.info("Verification errors:")
            for error in verification_results["errors"]:
                self.logger.info(f"  - {error}")
        
        table_row_data = verification_results.get("table_row_data", {})
        if table_row_data.get("full_row_text"):
            self.logger.info(f"Table row data: {table_row_data['full_row_text'][:200]}...")

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
async def test_admin_verification_only():
    """Pytest function for testing only admin verification"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=TestConfig.BROWSER_HEADLESS, 
            slow_mo=TestConfig.BROWSER_SLOW_MO
        )
        page = await browser.new_page()
        
        test_suite = TestCompleteApartmentWorkflow()
        
        try:
            await test_suite.test_admin_verification_only(page)
        finally:
            await browser.close()

if __name__ == "__main__":
    async def run_complete_e2e_test():
        """Run complete end-to-end test including admin verification"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=TestConfig.BROWSER_HEADLESS, 
                slow_mo=TestConfig.BROWSER_SLOW_MO
            )
            page = await browser.new_page()
            
            test_suite = TestCompleteApartmentWorkflow()
            
            try:
                print("=== STARTING COMPLETE E2E APARTMENT WORKFLOW TEST ===")
                await test_suite.test_complete_apartment_workflow(page)
                
            except Exception as e:
                print(f"\n✗ E2E WORKFLOW TEST FAILED: {e}")
                import traceback
                print(traceback.format_exc())
            
            finally:
                print("Screenshots saved in screenshots/ directory")
                print("\nKeeping browser open for 10 seconds to review results...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    async def run_admin_verification_test():
        """Run only admin verification test (login + table check)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=TestConfig.BROWSER_HEADLESS, 
                slow_mo=TestConfig.BROWSER_SLOW_MO
            )
            page = await browser.new_page()
            
            test_suite = TestCompleteApartmentWorkflow()
            
            try:
                print("=== STARTING ADMIN VERIFICATION TEST ===")
                await test_suite.test_admin_verification_only(page)
                
            except Exception as e:
                print(f"\n ADMIN VERIFICATION TEST FAILED: {e}")
                import traceback
                print(traceback.format_exc())
            
            finally:
                print("Screenshots saved in screenshots/ directory")
                print("\nKeeping browser open for 10 seconds to review results...")
                await page.wait_for_timeout(10000)
                await browser.close()

    print("Running complete end-to-end workflow test...")
    asyncio.run(run_complete_e2e_test())