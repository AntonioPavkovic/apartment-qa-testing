from pathlib import Path

class TestConfig:
    """Central configuration for all test settings"""
    BASE_URL = "https://mostar.api.demo.ch.melon.market/"
    APPLICATION_FORM_URL = "https://mostar.demo.melon.market/form/application/new"
    FALLBACK_APPLICATION_URL = "https://mostar.demo.melon.market/form/application/new?uuids=e34bfbd2-218e-4f36-9e92-e2ae9367fcfc&lang=en"
    
    DEFAULT_TIMEOUT = 5000
    SLOW_TIMEOUT = 10000
    NETWORK_IDLE_TIMEOUT = 10000
    WAIT_BETWEEN_ACTIONS = 1000
    SCREENSHOT_DELAY = 500
    
    BROWSER_SLOW_MO = 1000
    BROWSER_HEADLESS = False

    SCREENSHOT_DIR = Path("screenshots")

    PARKING_PROBABILITY = 0.3
    CAR_SHARING_PROBABILITY = 0.2
    MOTORBIKE_PROBABILITY = 0.1
    BIKE_PARKING_PROBABILITY = 0.7
    ADDITIONAL_ROOM_PROBABILITY = 0.25
    STORAGE_ROOM_PROBABILITY = 0.4
    WORKSHOP_PROBABILITY = 0.15
    COWORKING_PROBABILITY = 0.25
    HOME_OFFICE_PROBABILITY = 0.6
    ACCESSIBILITY_PROBABILITY = 0.05


class Selectors:
    """CSS selectors organized by component"""

    APARTMENT_ROWS = [
        "tr[data-apartment-id]",
        "tr:has(td:has-text('Available'))",
        "tr:has(.bewerben)",
        "tr:has(span.bewerben)",
        "table tr:not(:first-child)",
        ".apartment-row",
        "tr:has(td):not(.header-row)"
    ]
    
    WISHLIST_BUTTONS = [
        "span.bewerben:has-text('Wishlist')",
        "span.bewerben",
        "span:has-text('Wishlist')",
        ".wishlist-btn",
        "[data-action='wishlist']"
    ]
    
    WISHLIST_PANEL = [
        ".apartments-table-wishlist",
        "[data-v-21a4b90e].apartments-table-wishlist",
        "div[class*='apartments-table-wishlist']"
    ]

    APPLY_BUTTONS = [
        ".button:has-text('Apply')",
        "[data-v-21a4b90e].button:has-text('Apply')",
        "div.button:has-text('Apply')",
        "button:has-text('Apply')",
        "*[class*='button']:has-text('Apply')"
    ]
    
    FORM_CONTAINER = ".application-form"
    SUBMIT_BUTTON = "div#application-btn-submit"
    
    FORM_INDICATORS = [
        ".application-form",
        "form",
        "input[type='text']",
        "textarea",
        "select",
        ".af-steps"
    ]
    
    START_BUTTONS = [
        "#start-application-btn",
        "button:has-text('Start')",
        ".start-btn",
        "input[type='submit']",
        ".begin-application"
    ]

    ERROR_MESSAGES = [
        ".error-message",
        ".validation-error",
        ".field-error",
        "[class*='error']"
    ]
    
    SUCCESS_INDICATORS = [
        "div#apartment_household .af-position.active",
        "[class*='success']",
        ".step-completed"
    ]