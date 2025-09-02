from playwright.async_api import Page, ElementHandle
from typing import List, Optional
import random
import re

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
        await self._highlight_selected_apartment(selected)
        
        self.logger.info(f"Selected apartment from {len(clickable_apartments)} clickable options")
        await self.screenshot_manager.capture(self.page, "02_apartment_selected")
        return selected
    
    async def _has_clickable_actions(self, apartment: ElementHandle) -> bool:
        """Check if apartment has clickable wishlist/apply buttons"""
        try:
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
        await self.page.wait_for_timeout(1000)
        await apartment.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(500)
    
    async def extract_apartment_details(self, apartment: ElementHandle) -> ApartmentDetails:
        """Extract apartment details from the selected element"""
        self.logger.info("Getting apartment details...")
        
        try:
            text_content = await apartment.text_content() or ""
            details = ApartmentDetails(full_text=text_content.strip())
            
            # Extract specific details using regex
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