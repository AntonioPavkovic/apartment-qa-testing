import asyncio
from playwright.async_api import async_playwright

from config.test_config import TestConfig
from data.factories import TestDataFactory
from pages.admin_login_page import AdminLoginPage
from pages.admin_applications_page import AdminApplicationsPage
from utils.logging import TestLogger
from utils.screenshot_manager import ScreenshotManager


class AdminVerificationTest:
    """Standalone test for admin panel verification functionality"""
    
    def __init__(self):
        self.logger = TestLogger("AdminVerificationTest")
        self.screenshot_manager = ScreenshotManager()
    
    async def run_admin_verification_test(self):
        """Run the admin verification test"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=TestConfig.BROWSER_HEADLESS,
                slow_mo=TestConfig.BROWSER_SLOW_MO
            )
            page = await browser.new_page()
            
            try:
                async with self.logger.log_phase("Test Data Generation"):
                    test_family_data = TestDataFactory.create_family_for_test_type("smoke")
                    test_form_data = TestDataFactory.create_realistic_applicant()
                    
                    main_applicant = test_family_data[0]
                    self.logger.info(f"Test applicant created: {main_applicant.first_name} {main_applicant.last_name}")
                    self.logger.info(f"Email: {main_applicant.email}")
                    self.logger.info(f"Move-in date: {main_applicant.move_in_date}")

                admin_login_page = AdminLoginPage(page, self.screenshot_manager, self.logger)
                admin_apps_page = AdminApplicationsPage(page, self.screenshot_manager, self.logger)

                async with self.logger.log_phase("Admin Login", applicant_name=f"{main_applicant.first_name} {main_applicant.last_name}"):
                    await admin_login_page.navigate_to_admin_login()
                    await admin_login_page.login_to_admin_panel()
                    self.logger.info("Admin login successful")
                
                async with self.logger.log_phase("Applications Page Navigation"):
                    await admin_apps_page.navigate_to_applications()
                    self.logger.info("Applications page loaded")
                
                async with self.logger.log_phase("Applications Table Analysis"):
                    table_summary = await admin_apps_page.get_applications_table_summary()
                    
                    total_applications = table_summary.get('total_applications', 0)
                    self.logger.info(f"Found {total_applications} applications in table")
                    
                    if table_summary.get('table_headers'):
                        self.logger.info(f"Table headers: {', '.join(table_summary['table_headers'])}")
                    
                    if table_summary.get('sample_rows'):
                        self.logger.info("Sample applications found in table")
                        for i, sample in enumerate(table_summary['sample_rows'][:3]):
                            self.logger.info(f"Sample {i+1}: {sample.get('row_text', 'No data')[:100]}...")
                    
                    if table_summary.get('errors'):
                        for error in table_summary['errors']:
                            self.logger.error(f"Table analysis error: {error}")

                async with self.logger.log_phase("Applicant Search and Verification", applicant_email=main_applicant.email):
                    self.logger.info(f"Searching for test applicant: {main_applicant.first_name} {main_applicant.last_name}")
                    verification_results = await admin_apps_page.click_applicant_row_and_verify_details(
                        test_family_data,
                        test_form_data
                    )

                async with self.logger.log_phase("Results Processing"):
                    found_in_table = verification_results.get('found_in_table', False)
                    row_clicked = verification_results.get('row_clicked', False)
                    detail_loaded = verification_results.get('detail_page_loaded', False)
                    
                    if found_in_table:
                        self.logger.info("TEST APPLICANT FOUND IN TABLE!")
                        
                        if row_clicked:
                            self.logger.info("Successfully clicked applicant row")
                            
                            if detail_loaded:
                                self.logger.info("Detail view loaded successfully")

                                data_matches = verification_results.get('data_matches', {})
                                self.logger.info(f"Name verification: {data_matches.get('name_found', False)}")
                                self.logger.info(f"Email verification: {data_matches.get('email_found', False)}")
                                self.logger.info(f"Date verification: {data_matches.get('date_found', False)}")
                                
                                self.logger.info(f"Email in detail view: {data_matches.get('email_found_in_detail', False)}")
                                self.logger.info(f"Phone in detail view: {data_matches.get('phone_found_in_detail', False)}")
                                self.logger.info(f"Address in detail view: {data_matches.get('address_found_in_detail', False)}")
                                self.logger.info(f"Move-in date in detail: {data_matches.get('move_in_date_found_in_detail', False)}")

                                detail_data = verification_results.get('detail_page_data', {})
                                if detail_data.get('emails_found'):
                                    self.logger.info(f"Emails found: {detail_data['emails_found']}")
                                if detail_data.get('phones_found'):
                                    self.logger.info(f"Phones found: {detail_data['phones_found']}")
                                if detail_data.get('dates_found'):
                                    self.logger.info(f"Dates found: {detail_data['dates_found']}")
                                
                            else:
                                self.logger.warning("Row clicked but detail view did not load")
                                self.logger.warning("The application might use a different detail view mechanism")
                        else:
                            self.logger.warning("Found applicant but could not click row")
                            
                        table_row_data = verification_results.get('table_row_data', {})
                        if table_row_data.get('full_row_text'):
                            self.logger.info(f"Table row data: {table_row_data['full_row_text'][:150]}...")
                    else:
                        self.logger.warning("Test applicant NOT FOUND in table")
                        self.logger.info("This is EXPECTED for this test since we didn't actually submit an application")
                    
                    if verification_results.get('errors'):
                        self.logger.warning("Verification warnings found:")
                        for error in verification_results['errors']:
                            self.logger.warning(error)
                
            except Exception as e:
                self.logger.error(f"ADMIN VERIFICATION TEST FAILED: {e}")
                await self.screenshot_manager.capture_error(page, "admin_verification_failure")
                import traceback
                self.logger.error(f"Stack trace: {traceback.format_exc()}")
                raise
                
            finally:
                self.logger.info("Screenshots saved in screenshots/ directory")
                await browser.close()

    async def run_verification_with_existing_page(self, page, family_data, form_data, logger, screenshot_manager):
        """Run verification logic with an existing page and data"""
        try:
            main_applicant = family_data[0]
            
            admin_login_page = AdminLoginPage(page, screenshot_manager, logger)
            admin_apps_page = AdminApplicationsPage(page, screenshot_manager, logger)

            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            logger.info("Already on admin panel, proceeding to applications...")
            
            async with logger.log_phase("Applications Page Navigation"):
                await admin_apps_page.navigate_to_applications()
                logger.info("Applications page loaded")
            
            async with logger.log_phase("Applications Table Analysis"):
                table_summary = await admin_apps_page.get_applications_table_summary()
                
                total_applications = table_summary.get('total_applications', 0)
                logger.info(f"Found {total_applications} applications in table")
                
                if table_summary.get('table_headers'):
                    logger.info(f"Table headers: {', '.join(table_summary['table_headers'])}")
                
                if table_summary.get('sample_rows'):
                    logger.info("Sample applications found in table")
                    for i, sample in enumerate(table_summary['sample_rows'][:3]):
                        logger.info(f"Sample {i+1}: {sample.get('row_text', 'No data')[:100]}...")
                
                if table_summary.get('errors'):
                    for error in table_summary['errors']:
                        logger.error(f"Table analysis error: {error}")

            async with logger.log_phase("Applicant Search and Verification", applicant_email=main_applicant.email):
                logger.info(f"Searching for test applicant: {main_applicant.first_name} {main_applicant.last_name}")
                verification_results = await admin_apps_page.click_applicant_row_and_verify_details(
                    family_data,
                    form_data
                )

            async with logger.log_phase("Results Processing"):
                found_in_table = verification_results.get('found_in_table', False)
                row_clicked = verification_results.get('row_clicked', False)
                detail_loaded = verification_results.get('detail_page_loaded', False)
                
                if found_in_table:
                    logger.info("TEST APPLICANT FOUND IN TABLE!")
                    
                    if row_clicked:
                        logger.info("Successfully clicked applicant row")
                        
                        if detail_loaded:
                            logger.info("Detail view loaded successfully")

                            data_matches = verification_results.get('data_matches', {})
                            logger.info(f"Name verification: {data_matches.get('name_found', False)}")
                            logger.info(f"Email verification: {data_matches.get('email_found', False)}")
                            logger.info(f"Date verification: {data_matches.get('date_found', False)}")
                            
                            logger.info(f"Email in detail view: {data_matches.get('email_found_in_detail', False)}")
                            logger.info(f"Phone in detail view: {data_matches.get('phone_found_in_detail', False)}")
                            logger.info(f"Address in detail view: {data_matches.get('address_found_in_detail', False)}")
                            logger.info(f"Move-in date in detail: {data_matches.get('move_in_date_found_in_detail', False)}")

                            detail_data = verification_results.get('detail_page_data', {})
                            if detail_data.get('emails_found'):
                                logger.info(f"Emails found: {detail_data['emails_found']}")
                            if detail_data.get('phones_found'):
                                logger.info(f"Phones found: {detail_data['phones_found']}")
                            if detail_data.get('dates_found'):
                                logger.info(f"Dates found: {detail_data['dates_found']}")
                            
                        else:
                            logger.warning("Row clicked but detail view did not load")
                            logger.warning("The application might use a different detail view mechanism")
                    else:
                        logger.warning("Found applicant but could not click row")
                        
                    table_row_data = verification_results.get('table_row_data', {})
                    if table_row_data.get('full_row_text'):
                        logger.info(f"Table row data: {table_row_data['full_row_text'][:150]}...")
                else:
                    logger.warning("Test applicant NOT FOUND in table")
                    logger.info("This could mean: 1) Application wasn't submitted, 2) Table structure changed, 3) Application is processed/hidden")
                
                if verification_results.get('errors'):
                    logger.warning("Verification warnings found:")
                    for error in verification_results['errors']:
                        logger.warning(error)

            await screenshot_manager.capture(page, "10_admin_verification_complete", full_page=True)
            logger.info("Admin verification phase completed successfully")
            
        except Exception as e:
            logger.error(f"ADMIN VERIFICATION FAILED: {e}")
            await screenshot_manager.capture_error(page, "admin_verification_failure")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

async def main():
    """Main execution function"""
    test = AdminVerificationTest()
    await test.run_admin_verification_test()


if __name__ == "__main__":
    print("Starting Admin Verification Test...")
    asyncio.run(main())