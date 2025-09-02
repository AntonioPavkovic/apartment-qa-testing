from playwright.async_api import Page, ElementHandle
from typing import List, Optional
import asyncio

from config.test_config import TestConfig
from utils.logging import TestLogger

class ElementInteractor:
    """Handles safe element interactions with retries and error handling"""
    
    def __init__(self, page: Page, logger: TestLogger):
        self.page = page
        self.logger = logger
    
    async def click_with_retry(self, selector: str, max_attempts: int = 3, timeout: int = TestConfig.DEFAULT_TIMEOUT) -> bool:
        """Click element with retry logic"""
        for attempt in range(max_attempts):
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    await self.page.wait_for_timeout(TestConfig.WAIT_BETWEEN_ACTIONS)
                    return True
            except Exception as e:
                self.logger.warning(f"Click attempt {attempt + 1} failed for {selector}: {e}")
                if attempt == max_attempts - 1:
                    return False
                await self.page.wait_for_timeout(1000)
        return False
    
    async def fill_field_safely(self, selector: str, value: str, clear_first: bool = True, typing_delay: int = 50) -> bool:
        """Fill form field with error handling"""
        try:
            await self.page.wait_for_selector(selector, timeout=TestConfig.DEFAULT_TIMEOUT)
            if clear_first:
                await self.page.fill(selector, "")
            await self.page.type(selector, value, delay=typing_delay)
            return True
        except Exception as e:
            self.logger.error(f"Failed to fill field {selector}: {e}")
            return False
    
    async def find_visible_elements(self, selectors: List[str]) -> List[ElementHandle]:
        """Find visible elements from a list of possible selectors"""
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                visible_elements = []
                for element in elements:
                    if await element.is_visible():
                        visible_elements.append(element)
                if visible_elements:
                    self.logger.info(f"Found elements using selector: {selector}")
                    return visible_elements
            except Exception as e:
                self.logger.warning(f"Selector {selector} failed: {e}")
                continue
        return []
    
    async def highlight_element(self, element: ElementHandle, color: str = "red"):
        """Highlight element for visual debugging"""
        await element.evaluate(f"el => el.style.border = '3px solid {color}'")
        await self.page.wait_for_timeout(TestConfig.SCREENSHOT_DELAY)