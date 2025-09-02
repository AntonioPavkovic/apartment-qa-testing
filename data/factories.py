import random

from config.test_config import TestConfig
from data.models import FormData, ParkingRequirements

class TestDataFactory:
    """Factory for creating test data scenarios"""
    
    PARKING_REASONS = [
        "Need car for work commute",
        "Family transportation needs",
        "Medical appointments",
        "Weekend travel",
        "Disabled family member transportation"
    ]
    
    ROOM_PURPOSES = [
        "Home office",
        "Guest bedroom",
        "Study room",
        "Art studio",
        "Music room",
        "Yoga/exercise space"
    ]
    
    STORAGE_PURPOSES = [
        "Seasonal items storage",
        "Sports equipment",
        "Documents and files",
        "Household items",
        "Hobby materials"
    ]
    
    WORKSHOP_PURPOSES = [
        "Art and painting",
        "Woodworking",
        "Photography",
        "Crafts and DIY",
        "Music production"
    ]
    
    HOME_OFFICE_REASONS = [
        "Remote work policy",
        "Freelance work",
        "Flexible work arrangement",
        "Better work-life balance",
        "Avoid commuting"
    ]
    
    ROOM_AREAS = ["10-15 m²", "15-20 m²", "8-12 m²", "12-18 m²"]
    STORAGE_AREAS = ["3-5 m²", "5-8 m²", "2-4 m²"]

    @classmethod
    def create_realistic_applicant(cls) -> FormData:
        """Create applicant with realistic random requirements based on original probabilities"""
        parking = ParkingRequirements()
        
        if random.random() < TestConfig.PARKING_PROBABILITY:
            parking.wants_parking = True
            parking_fields = [
                ("regular_spaces", "regular"),
                ("small_spaces", "small"),
                ("large_spaces", "large"),
                ("electric_spaces", "electric"),
                ("outdoor_spaces", "outdoor")
            ]
            
            for field_name, _ in parking_fields:
                if random.random() < 0.4:
                    spaces = random.randint(1, 2)
                    setattr(parking, field_name, spaces)
            
            if random.random() < 0.6:
                parking.reason = random.choice(cls.PARKING_REASONS)
        
        form_data = FormData(parking=parking)
        
        form_data.wants_car_sharing = random.random() < TestConfig.CAR_SHARING_PROBABILITY
        
        if random.random() < TestConfig.MOTORBIKE_PROBABILITY:
            form_data.wants_motorbike_parking = True
            form_data.motorbike_spaces = 1
        
        if random.random() < TestConfig.BIKE_PARKING_PROBABILITY:
            form_data.wants_bike_parking = True
            form_data.bike_spaces = random.randint(1, 3)
            if random.random() < 0.3:
                form_data.electric_bike_spaces = random.randint(1, 2)
        
        if random.random() < TestConfig.ADDITIONAL_ROOM_PROBABILITY:
            form_data.wants_additional_room = True
            form_data.additional_room_purpose = random.choice(cls.ROOM_PURPOSES)
            form_data.additional_room_area = random.choice(cls.ROOM_AREAS)
        
        if random.random() < TestConfig.STORAGE_ROOM_PROBABILITY:
            form_data.wants_storage_room = True
            form_data.storage_room_purpose = random.choice(cls.STORAGE_PURPOSES)
            form_data.storage_room_area = random.choice(cls.STORAGE_AREAS)
        
        if random.random() < TestConfig.WORKSHOP_PROBABILITY:
            form_data.wants_workshop = True
            form_data.workshop_purpose = random.choice(cls.WORKSHOP_PURPOSES)
        
        form_data.wants_coworking = random.random() < TestConfig.COWORKING_PROBABILITY
        
        if random.random() < TestConfig.HOME_OFFICE_PROBABILITY:
            form_data.wants_home_office = True
            form_data.home_office_reason = random.choice(cls.HOME_OFFICE_REASONS)
        
        form_data.needs_obstacle_free = random.random() < TestConfig.ACCESSIBILITY_PROBABILITY
        
        return form_data

    @classmethod
    def create_minimal_applicant(cls) -> FormData:
        """Applicant with no special requirements"""
        return FormData()

    @classmethod
    def create_maximalist_applicant(cls) -> FormData:
        """Applicant who wants everything"""
        parking = ParkingRequirements(
            wants_parking=True,
            regular_spaces=2,
            small_spaces=1,
            large_spaces=1,
            electric_spaces=1,
            electric_small_spaces=1,
            outdoor_spaces=1,
            special_spaces=1,
            reason="Business use and family transportation needs"
        )
        
        return FormData(
            parking=parking,
            wants_car_sharing=True,
            wants_motorbike_parking=True,
            motorbike_spaces=1,
            wants_bike_parking=True,
            bike_spaces=2,
            electric_bike_spaces=1,
            wants_additional_room=True,
            additional_room_purpose="Multi-purpose room for home office and guest accommodation",
            additional_room_area="15-25 m²",
            wants_storage_room=True,
            storage_room_purpose="Storage for seasonal items, sports equipment, and household goods",
            storage_room_area="5-10 m²",
            wants_workshop=True,
            workshop_purpose="Creative studio for art, crafts, and DIY projects",
            wants_coworking=True,
            wants_home_office=True,
            home_office_reason="Full-time remote work arrangement with video conferencing needs",
            needs_obstacle_free=True
        )

    @classmethod
    def create_invalid_data_applicant(cls) -> FormData:
        """Applicant with invalid data for validation testing"""
        parking = ParkingRequirements(
            wants_parking=True,
            regular_spaces=-5,
            reason="x" * 1000 
        )
        
        return FormData(parking=parking)