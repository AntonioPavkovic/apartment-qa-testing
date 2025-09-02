from pathlib import Path
from datetime import datetime
from playwright.async_api import Page

from config.test_config import TestConfig

class ScreenshotManager:
    """Manages screenshot capture and organization"""
    
    def __init__(self, base_dir: Path = TestConfig.SCREENSHOT_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    async def capture(self, page: Page, name: str, full_page: bool = False) -> str:
        """Capture screenshot with automatic naming"""
        filename = f"{name}.png"
        file_path = self.base_dir / filename
        
        await page.screenshot(path=str(file_path), full_page=full_page)
        return str(file_path)
    
    async def capture_error(self, page: Page, error_context: str) -> str:
        """Capture error screenshot with context"""
        return await self.capture(page, f"error_{error_context}", full_page=True)
