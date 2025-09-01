from playwright.async_api import Page, expect

class ApplicationFormPage:
    def __init__(self, page: Page):
        self.page = page
        self.start_button = page.locator("#start-application_btn")
        self.form_inputs = page.locator("input, textarea, select")

    async def click_start(self):
        """Click the Start button to begin the application"""
        await expect(self.start_button).to_be_visible()
        await self.start_button.click()

    async def is_form_ready(self) -> bool:
        """Check if the form is loaded by verifying first input field"""
        first_field = self.form_inputs.first
        await expect(first_field).to_be_visible()
        return True

    async def fill_form(self, data: dict):
        """Fill out the form with provided data (key: selector, value: text)"""
        for selector, value in data.items():
            field = self.page.locator(selector)
            await expect(field).to_be_visible()
            await field.fill(value)
        return True

    async def submit_form(self, submit_selector: str):
        """Click the submit button and wait for confirmation"""
        submit_button = self.page.locator(submit_selector)
        await expect(submit_button).to_be_visible()
        await submit_button.click()
