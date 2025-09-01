import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import random
import string
from datetime import datetime
import re

class TestWishlistWorkflow:
    """Simplified test based on actual HTML structure"""

    @pytest.fixture(scope="session")
    async def browser_setup(self):
        """Set up a single browser instance for all tests in the session."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def page(self, browser_setup: Browser):
        """Provide a new page for each test."""
        context = await browser_setup.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    async def test_wishlist_workflow_simple(self, page: Page):
        """Simple wishlist workflow test"""
        print("=== SIMPLE WISHLIST WORKFLOW TEST ===")
        
        try:
            print("1. Navigating to homepage...")
            await page.goto("https://mostar.api.demo.ch.melon.market/")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="screenshots/01_homepage.png")
            print("    Homepage loaded")

            print("2. Finding and clicking wishlist elements...")
            wishlist_selectors = [
                "span.bewerben:has-text('Wishlist')",
                "span[class*='bewerben']", 
                "td span:has-text('Wishlist')",
                "*:has-text('Wishlist')"
            ]
            
            first_wishlist = None
            for selector in wishlist_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    visible_elements = [el for el in elements if await el.is_visible()]
                    if visible_elements:
                        first_wishlist = visible_elements[0]
                        print(f" Found and using a wishlist element with selector: {selector}")
                        break
                except Exception:
                    continue
            
            if not first_wishlist:
                print(" No visible wishlist elements found. Exiting test.")
                pytest.fail("Failed to find a visible wishlist element.")

            await first_wishlist.evaluate("el => el.style.backgroundColor = 'yellow'")
            await page.wait_for_timeout(1000)
            await first_wishlist.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="screenshots/02_wishlist_clicked.png")
            print(" Wishlist element clicked")

            print("3. Looking for wishlist panel...")
            await self.find_wishlist_panel(page)

            print("4. Finding and clicking Apply button to open a new page...")
            new_page = await self.find_and_click_apply(page)
            if not new_page:
                print(" Test failed: Could not click Apply button or open a new page.")
                await page.screenshot(path="screenshots/error_apply_failed.png", full_page=True)
                pytest.fail("Failed to navigate to the application form.")

            page = new_page
            await page.bring_to_front()

            print("5. Verifying URL and form elements on the new page...")
            await page.wait_for_url(re.compile("form/application/new"), timeout=10000)
            
            print(" Successfully navigated to application form!")
            await page.screenshot(path="screenshots/03_form_page_loaded.png", full_page=True)

            print("6. Looking for Start button...")
            start_btn = page.locator("#start-application-btn")
            await start_btn.wait_for(state="visible", timeout=5000)
            await page.screenshot(path="screenshots/04_start_button.png", full_page=True)
            print(" Start button visible")

            await start_btn.click()
            await page.wait_for_timeout(3000)
            print(" Start button clicked")

            print("7. Verifying form started...")
            form_field = page.locator("input, textarea, select").first
            await form_field.wait_for(state="visible", timeout=5000)
            await page.screenshot(path="screenshots/05_form_started.png", full_page=True)
            print(" Application form started successfully")

        except Exception as e:
            await page.screenshot(path="screenshots/error_final.png", full_page=True)
            print(f"Test failed with an exception: {e}")
            raise

    async def debug_page_structure(self, page: Page):
        """Debug helper to understand page structure"""
        print("   DEBUGGING PAGE STRUCTURE:")
        
        wishlist_text_elements = await page.query_selector_all("*")
        wishlist_matches = []
        
        for element in wishlist_text_elements[:50]:
            try:
                text = await element.text_content()
                if text and "Wishlist" in text:
                    tag_name = await element.evaluate("el => el.tagName")
                    class_name = await element.get_attribute("class") or "no-class"
                    is_visible = await element.is_visible()
                    wishlist_matches.append(f" {tag_name}.{class_name} (visible: {is_visible}): '{text.strip()[:50]}'")
            except:
                continue
        
        print(f"  Elements containing 'Wishlist': {len(wishlist_matches)}")
        for match in wishlist_matches[:5]:
            print(match)
        
        tables = await page.query_selector_all("table")
        print(f"  Tables found: {len(tables)}")
        
        buttons = await page.query_selector_all("button")
        spans = await page.query_selector_all("span")
        print(f" Buttons found: {len(buttons)}")
        print(f" Spans found: {len(spans)}")

    async def find_wishlist_panel(self, page: Page):
        """Find the wishlist panel that should appear"""
        try:
            panel_selectors = [
                ".apartments-table-wishlist",
                "[data-v-21a4b90e].apartments-table-wishlist",
                "div[class*='wishlist']",
                "*:has-text('1/3')",
                ".wishlist-header"
            ]
            
            for selector in panel_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        print(f" Wishlist panel found: {selector}")
                        return True
                except:
                    continue
            
            apply_elements = await page.query_selector_all("*:has-text('Apply')")
            visible_apply = [el for el in apply_elements if await el.is_visible()]
            
            if visible_apply:
                print(f" Apply elements found: {len(visible_apply)}")
                return True
            
            print(" Wishlist panel not clearly detected")
            return False
            
        except Exception as e:
            print(f"  Error finding panel: {e}")
            return False

    async def find_and_click_apply(self, page: Page):
        """Find and click the Apply button, waiting for a new page."""
        try:
            apply_selectors = [
                ".button:has-text('Apply')",
                "[data-v-21a4b90e].button:has-text('Apply')", 
                "div.button:has-text('Apply')",
                "button:has-text('Apply')",
                "*[class*='button']:has-text('Apply')"
            ]
            
            for selector in apply_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        print(f"  Apply button found: {selector}")
                        await element.evaluate("el => el.style.border = '3px solid red'")
                        await page.wait_for_timeout(1000)
                        
                        async with page.context.expect_page() as new_page_info:
                            await element.click()
                        
                        new_page = await new_page_info.value
                        print("    New page/tab opened successfully.")
                        return new_page
            
            print(" No clickable Apply button found or new page failed to open.")
            return None
            
        except Exception as e:
            print(f"  Error finding or clicking Apply button: {e}")
            return None

if __name__ == "__main__":
    async def run_simple_test():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1500)
            page = await browser.new_page()
            
            test_suite = TestWishlistWorkflow()
            
            try:
                await test_suite.test_wishlist_workflow_simple(page)
                print("\n WISHLIST WORKFLOW TEST COMPLETED SUCCESSFULLY!")
            except Exception as e:
                print(f"\n WISHLIST WORKFLOW TEST FAILED: {e}")
            finally:
                print(" Screenshots saved in screenshots/ directory")
                print("\nKeeping browser open for 10 seconds to review results...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    print(" Starting simple wishlist workflow test...")
    asyncio.run(run_simple_test())