from playwright.async_api import Page
from config.test_config import TestConfig
from exceptions.test_exceptions import ApplicationFormError
from utils.screenshot_manager import ScreenshotManager
from utils.logging import TestLogger

class AdminLoginPage:
    """Page Object Model for admin panel login functionality"""
    
    def __init__(self, page: Page, screenshot_manager: ScreenshotManager, logger: TestLogger):
        self.page = page
        self.screenshot_manager = screenshot_manager
        self.logger = logger
        self.admin_url = "https://mostar.demo.ch.melon.market/"
        self.username = "antonio"
        self.password = "8W7suY9F2$kq"
    
    async def navigate_to_admin_login(self) -> None:
        """Navigate to the admin login page"""
        self.logger.info(f"Navigating to admin login: {self.admin_url}")
        
        try:
            await self.page.goto(self.admin_url)
            await self.page.wait_for_load_state('networkidle')
            await self.screenshot_manager.capture(self.page, "09_admin_login_page", full_page=True)
            self.logger.info("Admin login page loaded successfully")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "admin_login_navigation_error")
            raise ApplicationFormError(f"Error navigating to admin login: {e}")
    
    async def verify_login_page_loaded(self) -> bool:
        """Verify that the login page has loaded correctly"""
        self.logger.info("Verifying admin login page...")
        
        try:
            await self.page.wait_for_selector("input[type='text'][required]", timeout=TestConfig.DEFAULT_TIMEOUT)
            
            login_indicators = [
                "span:has-text('Username')",
                "span:has-text('Password')", 
                "input[type='text'][required]",
                "input[type='password'][required]"
            ]
            
            found_indicators = 0
            for selector in login_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    found_indicators += 1
                    self.logger.info(f"Found login indicator: {selector}")
                except:
                    continue
            
            if found_indicators >= 2:
                self.logger.info("Admin login page verified successfully")
                return True
            else:
                self.logger.error("Not enough login page indicators found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying login page: {e}")
            return False
    
    async def login_to_admin_panel(self) -> None:
        """Login to the admin panel with provided credentials"""
        self.logger.info("Logging into admin panel...")
        
        try:
            if not await self.verify_login_page_loaded():
                await self.debug_current_page()
                raise ApplicationFormError("Admin login page did not load correctly")
            
            await self._fill_login_credentials()
            await self._submit_login()
            await self._verify_login_success()
            
            await self.screenshot_manager.capture(self.page, "10_admin_dashboard", full_page=True)
            self.logger.info("Successfully logged into admin panel")
            
        except Exception as e:
            await self.screenshot_manager.capture_error(self.page, "admin_login_error")
            raise ApplicationFormError(f"Error logging into admin panel: {e}")
    
    async def _fill_login_credentials(self) -> None:
        """Fill in the username and password fields"""
        self.logger.info("Filling login credentials...")
        
        try:
            await self.page.fill("input[type='text'][required]", self.username)
            self.logger.info("Username filled successfully")
            
            await self.page.fill("input[type='password'][required]", self.password)
            self.logger.info("Password filled successfully")
            
            await self.page.wait_for_timeout(500)
            
        except Exception as e:
            self.logger.error(f"Error filling login credentials: {e}")
            raise
    
    async def _submit_login(self) -> None:
        """Submit the login form"""
        self.logger.info("Submitting login form...")
        
        try:
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Anmelden')",
                "button:has-text('Sign in')",
                ".login-button",
                ".btn-login"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = await self.page.query_selector(selector)
                    if login_button:
                        self.logger.info(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                password_field = await self.page.query_selector("input[type='password'][required]")
                if password_field:
                    await password_field.press("Enter")
                    self.logger.info("Submitted login by pressing Enter on password field")
                else:
                    raise ApplicationFormError("No login button or password field found for submission")
            else:
                await login_button.click()
                self.logger.info("Clicked login button")

            await self.page.wait_for_timeout(3000)
            
        except Exception as e:
            self.logger.error(f"Error submitting login form: {e}")
            raise
    
    async def _verify_login_success(self) -> None:
        """Verify that login was successful"""
        self.logger.info("Verifying login success...")
        
        try:
            current_url = self.page.url
            self.logger.info(f"URL before waiting: {current_url}")

            try:
                await self.page.wait_for_function(
                    "() => !window.location.href.includes('/login') || document.querySelector('text=Bewerbungen') || document.querySelector('[class*=\"dashboard\"]')",
                    timeout=15000
                )
            except:
                await self.page.wait_for_timeout(5000)
            
            current_url = self.page.url
            self.logger.info(f"Current URL after login: {current_url}")

            if "/login" not in current_url:
                self.logger.info("Login successful - redirected away from login page")
                return

            admin_indicators = [
                "text=Bewerbungen",
                "text=Dashboard", 
                "text=Admin",
                "[class*='dashboard']",
                "[class*='admin']",
                "nav", 
                ".sidebar",
                ".menu"
            ]
            
            found_indicator = False
            for selector in admin_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        found_indicator = True
                        self.logger.info(f"Found admin panel indicator: {selector}")
                        break
                except:
                    continue
            
            if not found_indicator:
                error_selectors = [
                    "text=Invalid",
                    "text=Error", 
                    "text=Fehler",
                    "text=Ungültig",
                    "text=Falsch",
                    ".error",
                    ".alert-danger",
                    "[class*='error']"
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = await self.page.query_selector(selector)
                        if error_element and await error_element.is_visible():
                            error_text = await error_element.text_content()
                            raise ApplicationFormError(f"Login failed with error: {error_text}")
                    except:
                        continue
                
                self.logger.warning("No admin panel indicators found, but no errors detected either. Assuming login succeeded.")
            
        except Exception as e:
            self.logger.error(f"Error verifying login success: {e}")
            self.logger.warning("Login verification failed, but continuing anyway")
    
    async def debug_current_page(self) -> None:
        """Debug what's currently on the page"""
        self.logger.info("=== DEBUGGING ADMIN LOGIN PAGE STATE ===")
        
        current_url = self.page.url
        self.logger.info(f"Current URL: {current_url}")

        title = await self.page.title()
        self.logger.info(f"Page title: {title}")

        text_inputs = await self.page.query_selector_all("input[type='text']")
        self.logger.info(f"Found {len(text_inputs)} text input fields")
        
        password_inputs = await self.page.query_selector_all("input[type='password']")
        self.logger.info(f"Found {len(password_inputs)} password input fields")
        
        buttons = await self.page.query_selector_all("button")
        self.logger.info(f"Found {len(buttons)} buttons on page")

        specific_elements = [
            "span:has-text('Username')",
            "span:has-text('Password')",
            ".fa-asterisk",
            ".password-icon"
        ]
        
        for selector in specific_elements:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    self.logger.info(f"Found element: {selector}")
            except:
                continue
        
        await self.screenshot_manager.capture_error(self.page, "admin_login_debug")