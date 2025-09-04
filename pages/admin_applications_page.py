from playwright.async_api import Page
from typing import Dict, List, Optional, Any
from config.test_config import TestConfig
from exceptions.test_exceptions import ApplicationFormError
from utils.screenshot_manager import ScreenshotManager
from utils.logging import TestLogger
from data.models import PersonData, FormData

class AdminApplicationsPage:
    """Page Object Model for admin applications management functionality"""
    
    def __init__(self, page: Page, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.screenshot_manager = screenshot_manager
        self.logger = logger
        self.applications_url = "https://mostar.demo.ch.melon.market/applications"
    
    async def navigate_to_applications(self) -> None:
        """Navigate to the applications page from admin dashboard"""
        self.logger.info(f"Navigating to applications page: {self.applications_url}")
        
        try:
            await self._try_navigation_menu()

            current_url = self.page.url
            if "/applications" not in current_url:
                self.logger.info("Navigation menu not found, trying direct URL navigation")
                await self.page.goto(self.applications_url)

            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                self.logger.info("Page domcontentloaded state reached")
            except:
                self.logger.warning("domcontentloaded timeout, but continuing...")

            await self.page.wait_for_timeout(3000)
            
            await self.screenshot_manager.capture(self.page, "11_applications_page", full_page=True)
            
            if not await self._verify_applications_page_loaded():
                raise ApplicationFormError("Applications page did not load correctly")
            
            self.logger.info("Successfully navigated to applications page")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "applications_navigation_error")
            raise ApplicationFormError(f"Error navigating to applications page: {e}")
    
    async def _try_navigation_menu(self) -> None:
        """Try to navigate using the admin menu/navigation"""
        self.logger.info("Attempting navigation via admin menu...")

        navigation_selectors = [
            "a[href='/applications']",
            "a[href='/applications'].menu-item-parent",
            "div.menu-item a[href='/applications']",
            ".menu-item a[href='/applications']",
            ".menu-item-label:has-text('Applications')",
            "span.menu-item-label:has-text('Applications')",
            "text=Applications",
            "span:has-text('Applications')"
        ]
        
        for selector in navigation_selectors:
            try:
                self.logger.info(f"Trying selector: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element and await element.is_visible():
                    self.logger.info(f"Found visible element with selector: {selector}")
                    await element.click()
                    self.logger.info(f"Successfully clicked navigation element: {selector}")
                    await self.page.wait_for_timeout(2000)
                    
                    current_url = self.page.url
                    if "/applications" in current_url:
                        self.logger.info(f"Navigation successful: {current_url}")
                        return
                    else:
                        self.logger.info(f"Click succeeded but URL unchanged: {current_url}")
                        
            except Exception as e:
                self.logger.info(f"Selector failed: {selector} - {e}")
                continue
        
        # JavaScript fallback if CSS selectors fail
        self.logger.info("CSS selectors failed, trying JavaScript approach...")
        try:
            await self.page.evaluate("""
                // Find Appointments link by href first
                const appointmentLinks = document.querySelectorAll('a[href="/viewing-appointments"]');
                if (appointmentLinks.length > 0) {
                    console.log('Found Appointments link, clicking...');
                    appointmentLinks[0].click();
                    return;
                }
                
                // Find Applications link by href
                const appLinks = document.querySelectorAll('a[href="/applications"]');
                if (appLinks.length > 0) {
                    console.log('Found Applications link, clicking...');
                    appLinks[0].click();
                    return;
                }
                
                // Find by text content - try both
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.textContent && (el.textContent.trim() === 'Appointments' || el.textContent.trim() === 'Applications')) {
                        const clickableParent = el.closest('a, button, [onclick]');
                        if (clickableParent) {
                            console.log('Found text, clicking parent...');
                            clickableParent.click();
                            return;
                        }
                    }
                }
            """)
            
            await self.page.wait_for_timeout(2000)
            current_url = self.page.url
            if "/viewing-appointments" in current_url or "/applications" in current_url:
                self.logger.info("JavaScript navigation succeeded")
                return
                
        except Exception as e:
            self.logger.info(f"JavaScript navigation failed: {e}")
        
        self.logger.info("No navigation menu items found")
    
    async def _verify_applications_page_loaded(self) -> bool:
        """Verify that the applications page has loaded correctly"""
        self.logger.info("Verifying applications page loaded...")
        
        try:
            current_url = self.page.url
            if "/applications" in current_url or "/bewerbungen" in current_url:
                self.logger.info("URL indicates applications page loaded")
                return True
            
            page_indicators = [
                "text=Bewerbungen",
                "text=Applications", 
                "table",
                ".table",
                "[data-testid*='applications']",
                "[data-testid*='bewerbungen']",
                "th:has-text('Name')",
                "th:has-text('Email')",
                "th:has-text('Status')"
            ]
            
            found_indicators = 0
            for selector in page_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    found_indicators += 1
                    self.logger.info(f"Found applications page indicator: {selector}")
                except:
                    continue
            
            if found_indicators >= 1:
                self.logger.info("Applications page verified successfully")
                return True
            else:
                self.logger.error("Applications page indicators not found")
                await self._debug_applications_page()
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying applications page: {e}")
            return False
    
    async def verify_applicant_in_table(self, expected_data: List[PersonData], form_data: FormData = None) -> Dict[str, Any]:
        """
        Verify that the submitted applicant appears in the applications table
        
        Args:
            expected_data: List of PersonData objects (adults and children)
            form_data: Optional FormData for additional verification
            
        Returns:
            Dict with verification results
        """
        self.logger.info("Verifying applicant appears in applications table...")
        
        verification_results = {
            "found_in_table": False,
            "data_matches": {},
            "errors": [],
            "table_row_data": {}
        }
        
        try:
            await self._wait_for_applications_table()
            
            main_applicant = expected_data[0] if expected_data else None
            if not main_applicant:
                verification_results["errors"].append("No main applicant data provided for verification")
                self.logger.error("No main applicant data provided for verification")
                return verification_results
            
            table_row = await self._find_applicant_row(main_applicant)
            if not table_row:
                verification_results["errors"].append("Applicant not found in applications table")
                self.logger.warning("Applicant not found in applications table")

                await self._debug_table_contents()
                await self.screenshot_manager.capture_error(self.page, "applicant_not_found_in_table")
                return verification_results
            
            verification_results["found_in_table"] = True
            self.logger.info("Applicant found in applications table")

            row_data = await self._extract_row_data(table_row)
            verification_results["table_row_data"] = row_data

            data_verification = await self._verify_table_data(row_data, main_applicant, expected_data, form_data)
            verification_results["data_matches"] = data_verification
            
            await self.screenshot_manager.capture(self.page, "12_applicant_verified_in_table", full_page=True)
            self.logger.info("Applicant verification completed successfully")
            
            return verification_results
            
        except Exception as e:
            verification_results["errors"].append(f"Error during verification: {str(e)}")
            await self.screenshot_manager.capture_error(self.page, "applicant_verification_error")
            self.logger.error(f"Error verifying applicant in table: {e}")
            return verification_results
    
    async def _wait_for_applications_table(self) -> None:
        """Wait for the applications table to load"""
        self.logger.info("Waiting for applications table to load...")
        
        table_selectors = [
            "table",
            ".table",
            "[role='table']",
            ".applications-table",
            ".bewerbungen-table"
        ]
        
        table_found = False
        for selector in table_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=15000)
                table_found = True
                self.logger.info(f"Applications table found with selector: {selector}")
                break
            except:
                continue
        
        if not table_found:
            content_selectors = [
                "text=Bewerbungen",
                "text=Applications", 
                "tr", "td", "th",
                ".content", ".main-content"
            ]
            
            for selector in content_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    self.logger.info(f"Found page content with selector: {selector}")
                    table_found = True
                    break
                except:
                    continue
        
        if not table_found:
            self.logger.warning("No table found, but continuing with verification attempt...")

        await self.page.wait_for_timeout(3000)

    async def highlight_found_row(self, table_row) -> None:
        """Add a red border around the found applicant row"""
        try:
            await table_row.evaluate("""
                (element) => {
                    element.style.border = '3px solid red';
                    element.style.backgroundColor = '#ffebee';
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            """)
            await self.page.wait_for_timeout(2000)
            self.logger.info("Added red border around found applicant row")
        except Exception as e:
            self.logger.error(f"Error highlighting row: {e}")

    async def _find_applicant_row(self, main_applicant: PersonData) -> Optional[Any]:
        """Find the table row containing the main applicant"""
        self.logger.info(f"Looking for applicant: {main_applicant.first_name} {main_applicant.last_name}")

        search_strategies = [
            f"tr:has-text('{main_applicant.first_name} {main_applicant.last_name}')",
            f"tr:has-text('{main_applicant.last_name}, {main_applicant.first_name}')",
            f"tr:has-text('{main_applicant.email}')",
            f"tr:has-text('{main_applicant.last_name}')",
            f"tr:has-text('{main_applicant.first_name}')"
        ]
        
        for strategy in search_strategies:
            try:
                rows = await self.page.query_selector_all(strategy)
                if rows:
                    self.logger.info(f"Found {len(rows)} potential matches with strategy: {strategy}")
                    found_row = rows[0]
                
                    await self.highlight_found_row(found_row)
                    
                    return found_row
            except Exception as e:
                self.logger.debug(f"Strategy failed: {strategy} - {e}")
                continue

        self.logger.info("Trying manual search through all table rows...")
        found_row = await self._manual_row_search(main_applicant)

        if found_row:
            await self.highlight_found_row(found_row)
        
        return found_row

    
    async def _manual_row_search(self, main_applicant: PersonData) -> Optional[Any]:
        """Manually search through table rows when selectors fail"""
        try:
            rows = await self.page.query_selector_all("tr")
            self.logger.info(f"Searching through {len(rows)} table rows manually")
            
            for row in rows:
                try:
                    row_text = await row.text_content()
                    if row_text and (
                        main_applicant.last_name.lower() in row_text.lower() or
                        main_applicant.email.lower() in row_text.lower() or
                        (main_applicant.first_name.lower() in row_text.lower() and 
                         main_applicant.last_name.lower() in row_text.lower())
                    ):
                        self.logger.info(f"Found matching row with text: {row_text[:100]}...")
                        return row
                except:
                    continue
            
            self.logger.warning("No matching rows found in manual search")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in manual row search: {e}")
            return None
    
    async def _extract_row_data(self, table_row) -> Dict[str, str]:
        """Extract data from the table row"""
        self.logger.info("Extracting data from table row...")
        
        row_data = {}
        try:
            cells = await table_row.query_selector_all("td, th")
            
            row_text = await table_row.text_content()
            row_data["full_row_text"] = row_text.strip() if row_text else ""
            
            for i, cell in enumerate(cells):
                try:
                    cell_text = await cell.text_content()
                    if cell_text and cell_text.strip():
                        row_data[f"cell_{i}"] = cell_text.strip()
                except:
                    continue
            
            await self._identify_column_data(table_row, row_data)
            
            self.logger.info(f"Extracted row data: {row_data}")
            return row_data
            
        except Exception as e:
            self.logger.error(f"Error extracting row data: {e}")
            row_data["extraction_error"] = str(e)
            return row_data
    
    async def _identify_column_data(self, table_row, row_data: Dict[str, str]) -> None:
        """Try to identify specific column data like name, email, status"""
        try:
            full_text = row_data.get("full_row_text", "")

            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, full_text)
            if email_matches:
                row_data["email"] = email_matches[0]
            
            date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
            date_matches = re.findall(date_pattern, full_text)
            if date_matches:
                row_data["dates_found"] = date_matches

            status_keywords = ["pending", "approved", "rejected", "new", "submitted", "ausstehend", "genehmigt", "abgelehnt", "neu", "eingereicht"]
            for keyword in status_keywords:
                if keyword.lower() in full_text.lower():
                    row_data["status_indicator"] = keyword
                    break
            
        except Exception as e:
            self.logger.debug(f"Error identifying column data: {e}")
    
    async def _verify_table_data(self, row_data: Dict[str, str], main_applicant: PersonData, all_applicants: List[PersonData], form_data: FormData = None) -> Dict[str, bool]:
        """Verify that the table data matches expected applicant data"""
        self.logger.info("Verifying table data matches expected applicant data...")
        
        verification = {
            "name_found": False,
            "email_found": False,
            "date_found": False,
            "additional_data_found": False
        }
        
        try:
            full_text = row_data.get("full_row_text", "").lower()

            name_variants = [
                f"{main_applicant.first_name} {main_applicant.last_name}".lower(),
                f"{main_applicant.last_name}, {main_applicant.first_name}".lower(),
                f"{main_applicant.last_name}".lower(),
                f"{main_applicant.first_name}".lower()
            ]
            
            for name_variant in name_variants:
                if name_variant in full_text:
                    verification["name_found"] = True
                    self.logger.info(f"Name verified: {name_variant}")
                    break

            if main_applicant.email.lower() in full_text:
                verification["email_found"] = True
                self.logger.info("Email verified in table")

            if main_applicant.move_in_date and main_applicant.move_in_date in full_text:
                verification["date_found"] = True
                self.logger.info("Move-in date verified in table")
            
            if len(all_applicants) > 1:
                family_members_found = 0
                for applicant in all_applicants[1:]:
                    if (applicant.first_name.lower() in full_text or 
                        applicant.last_name.lower() in full_text):
                        family_members_found += 1
                
                if family_members_found > 0:
                    verification["additional_data_found"] = True
                    self.logger.info(f"Found {family_members_found} family members in table data")

            verified_count = sum(verification.values())
            total_checks = len(verification)
            self.logger.info(f"Data verification: {verified_count}/{total_checks} checks passed")
            
            return verification
            
        except Exception as e:
            self.logger.error(f"Error verifying table data: {e}")
            return verification
    
    async def get_applications_table_summary(self) -> Dict[str, Any]:
        """Get a summary of all applications in the table"""
        self.logger.info("Getting applications table summary...")
        
        summary = {
            "total_applications": 0,
            "table_headers": [],
            "sample_rows": [],
            "errors": []
        }
        
        try:
            await self._wait_for_applications_table()
            

            headers = await self.page.query_selector_all("th")
            for header in headers:
                try:
                    header_text = await header.text_content()
                    if header_text and header_text.strip():
                        summary["table_headers"].append(header_text.strip())
                except:
                    continue
            
            rows = await self.page.query_selector_all("tbody tr, table tr:not(:first-child)")
            summary["total_applications"] = len(rows)

            for i, row in enumerate(rows[:5]):
                try:
                    row_text = await row.text_content()
                    if row_text and row_text.strip():
                        summary["sample_rows"].append({
                            "row_index": i,
                            "row_text": row_text.strip()[:200]
                        })
                except:
                    continue
            
            self.logger.info(f"Table summary: {summary['total_applications']} applications found")
            return summary
            
        except Exception as e:
            summary["errors"].append(f"Error getting table summary: {str(e)}")
            self.logger.error(f"Error getting applications table summary: {e}")
            return summary
    
    async def _debug_applications_page(self) -> None:
        """Debug what's currently on the applications page"""
        self.logger.info("=== DEBUGGING APPLICATIONS PAGE STATE ===")
        
        try:
            current_url = self.page.url
            self.logger.info(f"Current URL: {current_url}")

            title = await self.page.title()
            self.logger.info(f"Page title: {title}")

            elements_to_check = [
                "table", "tr", "td", "th",
                ".table", ".applications", ".bewerbungen",
                "text=Bewerbungen", "text=Applications",
                "h1", "h2", "nav", ".sidebar"
            ]
            
            for selector in elements_to_check:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        if elements:
                            try:
                                text = await elements[0].text_content()
                                if text and len(text.strip()) > 0:
                                    self.logger.info(f"  Sample text: {text.strip()[:100]}")
                            except:
                                pass
                except:
                    continue
            
            await self.screenshot_manager.capture_error(self.page, "applications_page_debug")
            
        except Exception as e:
            self.logger.error(f"Error during applications page debug: {e}")
    
    async def _debug_table_contents(self) -> None:
        """Debug what's actually in the applications table"""
        self.logger.info("=== DEBUGGING TABLE CONTENTS ===")
        
        try:
            rows = await self.page.query_selector_all("tr")
            self.logger.info(f"Found {len(rows)} table rows total")
            
            for i, row in enumerate(rows[:10]):
                try:
                    row_text = await row.text_content()
                    if row_text and row_text.strip():
                        self.logger.info(f"Row {i}: {row_text.strip()[:150]}")
                except:
                    continue

            page_text = await self.page.text_content("body")
            if page_text:
                import re
                email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
                if email_matches:
                    self.logger.info(f"Found emails on page: {email_matches[:5]}")
                

                name_patterns = ["TestFamily", "John", "Sarah", "Emma"]
                for pattern in name_patterns:
                    if pattern.lower() in page_text.lower():
                        self.logger.info(f"Found name pattern '{pattern}' on page")
            
        except Exception as e:
            self.logger.error(f"Error debugging table contents: {e}")

    async def click_applicant_row_and_verify_details(self, expected_data: List[PersonData], form_data: FormData = None) -> Dict[str, Any]:
        """
        Find applicant row, click it, and verify detailed information
        
        Args:
            expected_data: List of PersonData objects (adults and children)
            form_data: Optional FormData for additional verification
            
        Returns:
            Dict with verification results including detailed data
        """
        self.logger.info("Finding and clicking applicant row to view details...")
        
        verification_results = {
            "found_in_table": False,
            "row_clicked": False,
            "detail_page_loaded": False,
            "data_matches": {},
            "errors": [],
            "table_row_data": {},
            "detail_page_data": {}
        }
        
        try:
            basic_verification = await self.verify_applicant_in_table(expected_data, form_data)
            verification_results.update(basic_verification)
            
            if not basic_verification.get("found_in_table", False):
                verification_results["errors"].append("Cannot click row - applicant not found in table")
                return verification_results
            
            main_applicant = expected_data[0] if expected_data else None
            if not main_applicant:
                verification_results["errors"].append("No main applicant data provided")
                return verification_results
            
            table_row = await self._find_applicant_row(main_applicant)
            if table_row:
                await self._click_table_row(table_row)
                verification_results["row_clicked"] = True
                
                detail_loaded = await self._wait_for_detail_view()
                verification_results["detail_page_loaded"] = detail_loaded
                
                if detail_loaded:
                    detail_data = await self._extract_detail_page_data()
                    verification_results["detail_page_data"] = detail_data
                    
                    detailed_verification = await self._verify_detailed_data(detail_data, main_applicant, expected_data, form_data)
                    verification_results["data_matches"].update(detailed_verification)
                    
                    await self.screenshot_manager.capture(self.page, "13_applicant_detail_view", full_page=True)
                    self.logger.info("Detailed applicant verification completed successfully")
                else:
                    verification_results["errors"].append("Detail view did not load after clicking row")
            
            return verification_results
            
        except Exception as e:
            verification_results["errors"].append(f"Error during detailed verification: {str(e)}")
            await self.screenshot_manager.capture_error(self.page, "detailed_verification_error")
            self.logger.error(f"Error in detailed verification: {e}")
            return verification_results

    async def _click_table_row(self, table_row) -> None:
        """Click on the table row to open details"""
        self.logger.info("Clicking table row to open details...")
        
        try:
            click_strategies = [
                lambda: table_row.click(),

                lambda: self._click_first_clickable_cell(table_row),

                lambda: self._click_row_action_element(table_row),
            ]
            
            for i, strategy in enumerate(click_strategies):
                try:
                    await strategy()
                    self.logger.info(f"Successfully clicked row using strategy {i+1}")
                    await self.page.wait_for_timeout(2000)
                    return
                except Exception as e:
                    self.logger.debug(f"Click strategy {i+1} failed: {e}")
                    continue
            
            try:
                await table_row.dblclick()
                self.logger.info("Successfully double-clicked row")
                await self.page.wait_for_timeout(2000)
            except Exception as e:
                self.logger.warning(f"All click strategies failed: {e}")
                raise Exception("Could not click table row")
                
        except Exception as e:
            self.logger.error(f"Error clicking table row: {e}")
            raise

    async def _click_first_clickable_cell(self, table_row) -> None:
        """Click the first clickable cell in the row"""
        cells = await table_row.query_selector_all("td")
        for cell in cells:
            try:
                links = await cell.query_selector_all("a, button, [onclick]")
                if links:
                    await links[0].click()
                    return
                
                await cell.click()
                return
            except:
                continue

        await table_row.click()

    async def _click_row_action_element(self, table_row) -> None:
        """Click a specific action element in the row (link, button, etc.)"""
        action_selectors = [
            "a",
            "button",
            "[data-action]",
            ".btn",
            ".link",
            "[onclick]",
            "td:first-child", 
        ]
        
        for selector in action_selectors:
            try:
                element = await table_row.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    self.logger.info(f"Clicked row element: {selector}")
                    return
            except:
                continue

        await table_row.click()

    async def _wait_for_detail_view(self) -> bool:
        """Wait for detail view/modal to load after clicking row"""
        self.logger.info("Waiting for detail view to load...")
        
        detail_indicators = [
            ".modal", ".dialog", ".popup", "[role='dialog']",
            
            "[class*='detail']", "[class*='application-detail']",
            
            lambda: "/detail" in self.page.url or "/application/" in self.page.url,
            
            "form", ".application-form", ".detail-form",
            
            "input[type='email']", "label:has-text('Email')", "label:has-text('Move-in')",
        ]
        
        for indicator in detail_indicators:
            try:
                if callable(indicator):
                    await self.page.wait_for_timeout(2000)
                    if indicator():
                        self.logger.info("Detail view loaded (URL changed)")
                        return True
                else:
                    await self.page.wait_for_selector(indicator, timeout=5000)
                    self.logger.info(f"Detail view loaded (found: {indicator})")
                    return True
            except:
                continue
        
        try:
            detail_content_selectors = [
                "text=Email", "text=Phone", "text=Address", "text=Move-in",
                "input", "textarea", "select",
            ]
            
            found_detail_content = 0
            for selector in detail_content_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        found_detail_content += len(elements)
                except:
                    continue
            
            if found_detail_content > 5:
                self.logger.info(f"Detail view likely loaded (found {found_detail_content} detail elements)")
                return True
        
        except Exception as e:
            self.logger.debug(f"Error checking for detail content: {e}")
        
        self.logger.warning("Detail view may not have loaded")
        return False

    async def _extract_detail_page_data(self) -> Dict[str, str]:
        """Extract detailed data from the detail view"""
        self.logger.info("Extracting data from detail view...")
        
        detail_data = {}
        
        try:
            page_text = await self.page.text_content("body")
            detail_data["full_page_text"] = page_text[:1000] if page_text else ""
            
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, page_text) if page_text else []
            if email_matches:
                detail_data["emails_found"] = email_matches
            
            phone_pattern = r'\b\d{2,3}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}\b'
            phone_matches = re.findall(phone_pattern, page_text) if page_text else []
            if phone_matches:
                detail_data["phones_found"] = phone_matches
            
            date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'
            date_matches = re.findall(date_pattern, page_text) if page_text else []
            if date_matches:
                detail_data["dates_found"] = date_matches
            
            form_data = await self._extract_form_field_values()
            if form_data:
                detail_data.update(form_data)
            
            labeled_data = await self._extract_labeled_information()
            if labeled_data:
                detail_data.update(labeled_data)
            
            self.logger.info(f"Extracted detail data: {len(detail_data)} fields found")
            return detail_data
            
        except Exception as e:
            self.logger.error(f"Error extracting detail page data: {e}")
            detail_data["extraction_error"] = str(e)
            return detail_data

    async def _extract_form_field_values(self) -> Dict[str, str]:
        """Extract values from form fields if present"""
        form_data = {}
        
        try:
            field_selectors = [
                "input[type='text']", "input[type='email']", "input[type='tel']",
                "input[type='date']", "textarea", "select"
            ]
            
            for selector in field_selectors:
                elements = await self.page.query_selector_all(selector)
                for i, element in enumerate(elements):
                    try:
                        value = await element.get_attribute("value") or await element.text_content()
                        name = await element.get_attribute("name") or await element.get_attribute("id")
                        
                        if value and value.strip():
                            key = name if name else f"{selector.replace('[', '_').replace(']', '').replace('=', '_')}_{i}"
                            form_data[key] = value.strip()
                    except:
                        continue
        
        except Exception as e:
            self.logger.debug(f"Error extracting form field values: {e}")
        
        return form_data

    async def _extract_labeled_information(self) -> Dict[str, str]:
        """Extract information that appears next to labels"""
        labeled_data = {}
        
        try:
            label_patterns = [
                ("Email", ["email", "e-mail", "@"]),
                ("Phone", ["phone", "tel", "mobile"]),
                ("Address", ["address", "street", "strasse"]),
                ("Move-in", ["move-in", "move in", "einzug"]),
                ("Date", ["date", "datum"]),
                ("Status", ["status", "state"]),
            ]
            
            page_text = await self.page.text_content("body")
            if not page_text:
                return labeled_data
            
            for label, patterns in label_patterns:
                for pattern in patterns:
                    import re
                    pattern_regex = rf'{pattern}:?\s*([^\n\r]+)'
                    matches = re.findall(pattern_regex, page_text, re.IGNORECASE)
                    if matches:
                        labeled_data[f"{label.lower()}_from_text"] = matches[0].strip()
                        break
        
        except Exception as e:
            self.logger.debug(f"Error extracting labeled information: {e}")
        
        return labeled_data

    async def _verify_detailed_data(self, detail_data: Dict[str, str], main_applicant: PersonData, all_applicants: List[PersonData], form_data: FormData = None) -> Dict[str, bool]:
        """Verify detailed data against expected applicant information"""
        self.logger.info("Verifying detailed data against expected applicant information...")
        
        detailed_verification = {
            "email_found_in_detail": False,
            "phone_found_in_detail": False,
            "address_found_in_detail": False,
            "move_in_date_found_in_detail": False,
            "additional_details_verified": False
        }
        
        try:
            emails_found = detail_data.get("emails_found", [])
            if main_applicant.email.lower() in [email.lower() for email in emails_found]:
                detailed_verification["email_found_in_detail"] = True
                self.logger.info(f"Email verified in detail view: {main_applicant.email}")
            
            phones_found = detail_data.get("phones_found", [])
            if main_applicant.phone_number:
                phone_clean = main_applicant.phone_number.replace(" ", "").replace("-", "")
                for phone in phones_found:
                    if phone_clean in phone.replace(" ", "").replace("-", ""):
                        detailed_verification["phone_found_in_detail"] = True
                        self.logger.info(f"Phone verified in detail view: {phone}")
                        break
            
            if main_applicant.street_and_number and main_applicant.city:
                full_page_text = detail_data.get("full_page_text", "").lower()
                if (main_applicant.street_and_number.lower() in full_page_text and 
                    main_applicant.city.lower() in full_page_text):
                    detailed_verification["address_found_in_detail"] = True
                    self.logger.info("Address verified in detail view")
            
            dates_found = detail_data.get("dates_found", [])
            if main_applicant.move_in_date and main_applicant.move_in_date in dates_found:
                detailed_verification["move_in_date_found_in_detail"] = True
                self.logger.info(f"Move-in date verified in detail view: {main_applicant.move_in_date}")
            
            if len(all_applicants) > 1:
                full_page_text = detail_data.get("full_page_text", "").lower()
                family_found_count = 0
                for applicant in all_applicants[1:]:
                    if (applicant.first_name.lower() in full_page_text and 
                        applicant.last_name.lower() in full_page_text):
                        family_found_count += 1
                
                if family_found_count > 0:
                    detailed_verification["additional_details_verified"] = True
                    self.logger.info(f"Found {family_found_count} family members in detail view")

            verified_count = sum(detailed_verification.values())
            total_checks = len(detailed_verification)
            self.logger.info(f"Detailed data verification: {verified_count}/{total_checks} checks passed")
            
            return detailed_verification
            
        except Exception as e:
            self.logger.error(f"Error verifying detailed data: {e}")
            return detailed_verification