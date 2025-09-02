class TestError(Exception):
    """Base exception for test-related errors"""
    pass

class ApartmentNotFoundError(TestError):
    """Raised when no apartments are available for testing"""
    pass

class ApplicationFormError(TestError):
    """Raised when application form issues occur"""
    pass

class NavigationError(TestError):
    """Raised when page navigation fails"""
    pass

class ElementInteractionError(TestError):
    """Raised when element interactions fail"""
    pass