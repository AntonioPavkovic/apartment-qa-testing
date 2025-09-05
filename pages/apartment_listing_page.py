from playwright.async_api import Page, ElementHandle
from typing import List, Optional
import random
import re
import asyncio

from config.test_config import Selectors, TestConfig
from data.models import ApartmentDetails
from exceptions.test_exceptions import ApartmentNotFoundError
from utils.element_interactor import ElementInteractor
from utils.logging import TestLogger
from utils.screenshot_manager import ScreenshotManager

class ApartmentListingPage:
    """Page Object Model for apartment listing functionality"""
    
    APARTMENT_KEYWORDS = ['available', 'rooms', 'apartment', 'flat', 'wishlist', 'apply']
    
    def __init__(self, page: Page, interactor: ElementInteractor, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.interactor = interactor
        self.screenshot_manager = screenshot_manager
        self.logger = logger
    
    async def navigate(self) -> None:
        """Navigate to the apartment listing page"""
        self.logger.info("Navigating to homepage...")
        await self.page.goto(TestConfig.BASE_URL)
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(3000)
        await self.screenshot_manager.capture(self.page, "01_homepage")
        self.logger.info("Homepage loaded")
    
    async def find_available_apartments(self) -> List[ElementHandle]:
        """Find all available apartments on the page"""
        self.logger.info("Exploring available apartments...")
        
        elements = await self.interactor.find_visible_elements(Selectors.APARTMENT_ROWS)
        
        apartments = []
        for element in elements:
            try:
                text_content = await element.text_content()
                if text_content and self._is_apartment_row(text_content):
                    apartments.append(element)
            except Exception as e:
                self.logger.warning(f"Error checking apartment element: {e}")
                continue
        
        if not apartments:
            raise ApartmentNotFoundError("No available apartments found on the page")
        
        self.logger.info(f"Found {len(apartments)} available apartments")
        return apartments
    
    def _is_apartment_row(self, text: str) -> bool:
        """Check if text content indicates an apartment row"""
        return any(keyword in text.lower() for keyword in self.APARTMENT_KEYWORDS)
    
    async def select_random_apartment(self, apartments: List[ElementHandle]) -> ElementHandle:
        """Select a random apartment from available ones"""
        self.logger.info("Selecting a random apartment...")
        
        clickable_apartments = []
        for apartment in apartments:
            if await self._has_clickable_actions(apartment):
                clickable_apartments.append(apartment)
                try:
                    title_text = await apartment.text_content()
                    apartment_id = title_text.split()[0] if title_text else "Unknown"
                    self.logger.info(f"Found clickable apartment: {apartment_id}")
                except:
                    self.logger.info("Found clickable apartment (ID unknown)")
        
        if not clickable_apartments:
            self.logger.warning("No apartments with clickable wishlist buttons found, trying all apartments")
            clickable_apartments = apartments
        
        selected = random.choice(clickable_apartments)

        await self._ensure_apartment_fully_visible(selected)
        await self._highlight_selected_apartment(selected)
        
        self.logger.info(f"Selected apartment from {len(clickable_apartments)} clickable options")
        await self.screenshot_manager.capture(self.page, "02_apartment_selected")
        return selected
    
    async def _ensure_apartment_fully_visible(self, apartment: ElementHandle) -> None:
        """Ensure the apartment and its action buttons are fully visible in viewport"""
        try:
            self.logger.info("Ensuring apartment is fully visible...")

            await apartment.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            
            apartment_box = await apartment.bounding_box()
            if not apartment_box:
                self.logger.warning("Could not get apartment bounding box")
                return
            
            viewport_size = self.page.viewport_size
            if not viewport_size:
                self.logger.warning("Could not get viewport size")
                return

            apartment_bottom = apartment_box['y'] + apartment_box['height']
            viewport_bottom = viewport_size['height']
            
            if apartment_bottom > viewport_bottom * 0.7:
                self.logger.info("Apartment is near bottom of screen, scrolling up to center it")
                
                scroll_offset = apartment_bottom - (viewport_bottom * 0.5)
                
                await self.page.evaluate(f"window.scrollBy(0, {scroll_offset})")
                await asyncio.sleep(1)

                await apartment.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)

            await self._ensure_apply_button_visible(apartment)
            
        except Exception as e:
            self.logger.warning(f"Error ensuring apartment visibility: {e}")
            await apartment.scroll_into_view_if_needed()
    
    async def _ensure_apply_button_visible(self, apartment: ElementHandle) -> None:
        """Ensure the apply button for this apartment is visible"""
        try:
            apply_buttons = await apartment.query_selector_all("span.bewerben, .apply-button, .wishlist-button")
            
            for button in apply_buttons:
                if await button.is_visible():
                    button_box = await button.bounding_box()
                    if button_box:
                        viewport_size = self.page.viewport_size
                        if viewport_size:
                            if button_box['y'] + button_box['height'] > viewport_size['height']:
                                self.logger.info("Apply button is below viewport, scrolling up")
                                scroll_amount = (button_box['y'] + button_box['height']) - viewport_size['height'] + 50
                                await self.page.evaluate(f"window.scrollBy(0, -{scroll_amount})")
                                await asyncio.sleep(0.5)

                            elif button_box['y'] < 0:
                                self.logger.info("Apply button is above viewport, scrolling down")
                                scroll_amount = abs(button_box['y']) + 50
                                await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                                await asyncio.sleep(0.5)
                    break
                    
        except Exception as e:
            self.logger.error(f"Error checking apply button visibility: {e}")
    
    async def _has_clickable_actions(self, apartment: ElementHandle) -> bool:
        """Check if apartment has clickable wishlist/apply buttons"""
        try:
            await apartment.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            
            wishlist_elements = await apartment.query_selector_all("span.bewerben")
            for element in wishlist_elements:
                if await element.is_visible():
                    classes = await element.get_attribute("class") or ""
                    if "disabled" not in classes.lower():
                        return True
            return False
        except Exception:
            return False
    
    async def _highlight_selected_apartment(self, apartment: ElementHandle) -> None:
        """Highlight the selected apartment visually"""
        await apartment.evaluate("el => el.style.backgroundColor = 'lightblue'")
        await apartment.evaluate("el => el.style.border = '2px solid blue'")
        await asyncio.sleep(1)
        
        await apartment.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
    
    async def click_apply_button(self, apartment: ElementHandle) -> bool:
        """Click the apply button for the selected apartment with improved visibility handling"""
        try:
            self.logger.info("Looking for apply button...")
            
            await self._ensure_apartment_fully_visible(apartment)
            
            apply_selectors = [
                "span.bewerben:not(.disabled)",
                ".apply-button:not(.disabled)",
                ".wishlist-button:not(.disabled)",
                "button:has-text('Apply'):not(.disabled)",
                "button:has-text('Bewerben'):not(.disabled)"
            ]
            
            for selector in apply_selectors:
                try:
                    buttons = await apartment.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible():
                            await button.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)

                            button_box = await button.bounding_box()
                            if button_box:
                                self.logger.info(f"Found clickable apply button with selector: {selector}")
                                await button.click()
                                await asyncio.sleep(1)
                                return True
                                
                except Exception as e:
                    self.logger.error(f"Apply button selector failed: {selector} - {e}")
                    continue
            
            self.logger.warning("No clickable apply button found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking apply button: {e}")
            return False
    
    async def smart_scroll_to_reveal_elements(self) -> None:
        """Smart scrolling to reveal hidden elements at page bottom"""
        try:
            self.logger.info("Performing smart scroll to reveal hidden elements...")
            
            page_metrics = await self.page.evaluate("""
                () => ({
                    scrollHeight: document.documentElement.scrollHeight,
                    clientHeight: document.documentElement.clientHeight,
                    scrollTop: window.pageYOffset || document.documentElement.scrollTop
                })
            """)
            
            if page_metrics['scrollTop'] + page_metrics['clientHeight'] > page_metrics['scrollHeight'] * 0.8:
                scroll_up_amount = page_metrics['clientHeight'] * 0.3
                self.logger.info(f"Near page bottom, scrolling up by {scroll_up_amount}px")
                await self.page.evaluate(f"window.scrollBy(0, -{scroll_up_amount})")
                await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Error in smart scroll: {e}")
    
    async def find_and_prepare_apartment_for_interaction(self, apartments: List[ElementHandle]) -> ElementHandle:
        """Find an apartment and prepare it for interaction (clicking apply button)"""
        self.logger.info("Finding and preparing apartment for interaction...")
        
        for apartment in apartments:
            try:
                await apartment.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                
                if await self._has_clickable_actions(apartment):
                    await self._ensure_apartment_fully_visible(apartment)
                    
                    apply_buttons = await apartment.query_selector_all("span.bewerben:not(.disabled)")
                    for button in apply_buttons:
                        if await button.is_visible():
                            button_box = await button.bounding_box()
                            if button_box: 
                                self.logger.info("Found apartment with accessible apply button")
                                await self._highlight_selected_apartment(apartment)
                                return apartment
                
            except Exception as e:
                self.logger.error(f"Error preparing apartment: {e}")
                continue

        self.logger.info("No apartments with immediately visible apply buttons, selecting random")
        selected = random.choice(apartments)
        await self._ensure_apartment_fully_visible(selected)
        await self._highlight_selected_apartment(selected)
        return selected
    
    async def extract_apartment_details(self, apartment: ElementHandle) -> ApartmentDetails:
        """Extract apartment details from the selected element"""
        self.logger.info("Getting apartment details...")
        
        try:
            text_content = await apartment.text_content() or ""
            details = ApartmentDetails(full_text=text_content.strip())
            self._extract_room_details(text_content, details)
            self._extract_price_details(text_content, details)
            self._extract_size_details(text_content, details)
            self._extract_status_details(text_content, details)
            self._extract_apartment_id(text_content, details)
            
            self.logger.info(f"Apartment details: {details}")
            return details
            
        except Exception as e:
            self.logger.error(f"Error extracting apartment details: {e}")
            return ApartmentDetails(full_text="Error extracting details")
    
    def _extract_room_details(self, text: str, details: ApartmentDetails) -> None:
        """Extract room information from text"""
        if room_match := re.search(r'(\d+(?:\.\d+)?)\s*(?:room|zimmer|Zimmer)', text, re.IGNORECASE):
            details.rooms = room_match.group(1)
    
    def _extract_price_details(self, text: str, details: ApartmentDetails) -> None:
        """Extract price information from text"""
        if price_match := re.search(r'(CHF|Fr\.?|€|\$)\s*(\d+(?:[,\.]\d+)*)', text, re.IGNORECASE):
            details.price = f"{price_match.group(1)}{price_match.group(2)}"
    
    def _extract_size_details(self, text: str, details: ApartmentDetails) -> None:
        """Extract size information from text"""
        if size_match := re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', text, re.IGNORECASE):
            details.size = f"{size_match.group(1)}m²"
    
    def _extract_status_details(self, text: str, details: ApartmentDetails) -> None:
        """Extract status information from text"""
        status_keywords = ['available', 'verfügbar', 'free', 'frei']
        if any(status in text.lower() for status in status_keywords):
            details.status = 'Available'
    
    def _extract_apartment_id(self, text: str, details: ApartmentDetails) -> None:
        """Extract apartment ID from text"""
        if id_match := re.search(r'^([A-Z0-9]+)', text.strip()):
            details.apartment_id = id_match.group(1)