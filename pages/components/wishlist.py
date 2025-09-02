from config.test_config import Selectors
from playwright.async_api import Page, ElementHandle  

from utils.element_interactor import ElementInteractor
from utils.logging import TestLogger
from utils.screenshot_manager import ScreenshotManager

class WishlistComponent:
    """Component for handling wishlist functionality"""
    
    def __init__(self, page: Page, interactor: ElementInteractor, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.interactor = interactor
        self.screenshot_manager = screenshot_manager
        self.logger = logger
    
    async def add_apartment(self, apartment: ElementHandle) -> bool:
        """Add apartment to wishlist"""
        self.logger.info("Adding apartment to wishlist...")
        
        try:
            wishlist_elements = await apartment.query_selector_all("span.bewerben")
            
            for element in wishlist_elements:
                if await element.is_visible():
                    classes = await element.get_attribute("class") or ""
                    if "disabled" in classes.lower():
                        self.logger.info("Wishlist button is disabled, skipping...")
                        return False
                    
                    await self.interactor.highlight_element(element, "yellow")
                    await element.click()
                    await self.page.wait_for_timeout(2000)
                    
                    await self.screenshot_manager.capture(self.page, "03_added_to_wishlist")
                    self.logger.info("Apartment added to wishlist")
                    return True
            
            self.logger.info("Could not add to wishlist, continuing with application...")
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding to wishlist: {e}")
            return False
    
    async def verify_wishlist_panel(self) -> bool:
        """Verify that wishlist panel appears after adding item"""
        self.logger.info("Waiting for wishlist panel to load...")
        
        try:
            for selector in Selectors.WISHLIST_PANEL:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        await self.screenshot_manager.capture(self.page, "03b_wishlist_panel")
                        self.logger.info(f"Wishlist panel found: {selector}")
                        return True
                except:
                    continue
            
            self.logger.warning("Wishlist panel not detected, but continuing...")
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying wishlist panel: {e}")
            return False