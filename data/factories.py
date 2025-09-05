import random
import time
import copy
from dataclasses import replace

from config.test_config import TestConfig
from data.models import FormData, HouseholdData, ParkingRequirements, PersonData

class TestDataFactory:
    """Factory for creating test data scenarios with reusable base objects"""
    
    COMPANY_CONTACTS = [
        "HR Manager", "Personnel Director", "Human Resources", 
        "Maria Schneider", "Thomas Mueller", "Anna Weber",
        "Stefan Fischer", "Nicole Graf", "Daniel Keller"
    ]

    DROPDOWN_OPTIONS = {
        'salutation': ['Mr.', 'Ms.'],
        'civil_status': ['Single', 'Married', 'Separated', 'Divorced', 'Widowed'],
        'residency_status': [
            '(B) Residence permit', 
            '(C) Long-term resident', 
            '(G) Frontier worker', 
            '(L) Short-stay resident', 
            '(N) Asylum seeker'
        ],
        'type_of_tenant': [
            'Main tenant', 
            'Spouse, registered partnership', 
            'Roommate, life partner', 
            'Guarantor', 
            'Subtenant'
        ],
        'employment_status': [
            'Full-time (90-100%)', 
            'Part-time (70-89%)', 
            'Part-time (50-69%)', 
            'Part-time (less than 50%)', 
            'Self-employed'
        ],
        'credit_check_type': [
            'CreditTrust certificate', 
            'Excerpt from debt collection'
        ]
    }

    SWISS_CITIES = [
        ('Zurich', '8001'), ('Basel', '4001'), ('Geneva', '1200'), 
        ('Bern', '3000'), ('Lausanne', '1000'), ('Winterthur', '8400'),
        ('Lucerne', '6000'), ('St. Gallen', '9000'), ('Lugano', '6900')
    ]
    
    SWISS_FIRST_NAMES = {
        'male': ['John', 'Michael', 'David', 'Marco', 'Stefan', 'Daniel'],
        'female': ['Sarah', 'Anna', 'Lisa', 'Elena', 'Nicole', 'Andrea'],
        'child_male': ['Liam', 'Noah', 'Lucas', 'Leon', 'Ben', 'Max'],
        'child_female': ['Emma', 'Sophie', 'Mia', 'Zoe', 'Lea', 'Nina']
    }
    
    SWISS_SURNAMES = ['Smith', 'Mueller', 'Weber', 'Fischer', 'Wagner', 'Schmid', 'Meier', 'Keller']

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

    HOUSEHOLD_TYPES = [
        "single person household",
        "couple household", 
        "couple household with child",
        "Single parent with child/ren",
        "Flat-share",
        "Other"
    ]

    RELOCATION_REASONS = [
        "Change of life situation",
        "Change in income",
        "Change in the place of work", 
        "Change in space requirements",
        "Noise / Emissions",
        "Price/performance ratio",
        "Problems with janitor/administration",
        "Problems with neighbors",
        "Reconstruction/Renovation",
        "Quality of living",
        "Termination by landlord",
        "Without a permanent residence",
        "Fixed term tenancy",
        "Other"
    ]
    
    COOPERATIVE_RELATIONS = [
        "Current tenant",
        "Child tenant", 
        "Voluntary member",
        "No relation"
    ]


    OBJECT_SOURCES = [
        "Real estate platform (Newhome, Erstbezug, Homegate, ...)",
        "Project website",
        "Facebook",
        "Instagram", 
        "LinkedIn"
    ]
    
    ROOM_AREAS = ["10-15 m²", "15-20 m²", "8-12 m²", "12-18 m²"]
    STORAGE_AREAS = ["3-5 m²", "5-8 m²", "2-4 m²"]


    @classmethod
    def create_realistic_household_data(cls) -> HouseholdData:
        return HouseholdData(
            household_type="couple household with child",
            has_pets=random.random() < 0.3,
            has_music_instruments=random.random() < 0.2, 
            is_smoker=random.random() < 0.15, 
            
            relocation_reason=random.choice(cls.RELOCATION_REASONS),
            desired_move_date="01.06.2024" if random.random() < 0.4 else None,
            mailbox_label="Smith Family" if random.random() < 0.6 else None,
            
            security_deposit_type="deposit" if random.random() < 0.8 else "insurance",
            income_rent_ratio=random.random() < 0.7, 
            iban="CH93 0076 2011 6238 5295 7" if random.random() < 0.5 else None,
            bank_name="UBS Switzerland" if random.random() < 0.5 else None,
            account_owner="John Smith" if random.random() < 0.5 else None,
            
            motivation="Looking for a community-oriented living space",
            participation_ideas="Interested in community garden and events" if random.random() < 0.6 else None,
            relation_to_cooperative=random.choice(cls.COOPERATIVE_RELATIONS) if random.random() < 0.4 else None,
            
            object_found_on=random.choice(cls.OBJECT_SOURCES),
            remarks="Excited to be part of the community!" if random.random() < 0.3 else None
        )

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
        
        form_data = FormData(parking=parking, household=cls.create_realistic_household_data(),)
        
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
    def create_family_with_child_data(cls, scenario: str = "default") -> list:
        """Create data for 2 adults and 1 child - simplified to only support default scenario"""
        return cls._create_random_family()

    @classmethod 
    def _create_random_family(cls) -> list:
        """Generate realistic random family data"""
        timestamp = int(time.time())
        family_name = random.choice(cls.SWISS_SURNAMES)
        city, postal_code = random.choice(cls.SWISS_CITIES)
        
        company_city, company_postcode = random.choice(cls.SWISS_CITIES)
        contact_person = random.choice(cls.COMPANY_CONTACTS)
        
        adult1 = PersonData(
            salutation=random.choice(cls.DROPDOWN_OPTIONS['salutation'][:2]),
            first_name=random.choice(cls.SWISS_FIRST_NAMES['male']),
            last_name=family_name,
            date_of_birth=f"{random.randint(1,28):02d}.{random.randint(1,12):02d}.{random.randint(1980,1990)}",
            civil_status=random.choice(cls.DROPDOWN_OPTIONS['civil_status'][:2]),
            nationality="Switzerland",
            residency_status=random.choice(cls.DROPDOWN_OPTIONS['residency_status'][:2]),
            type_of_tenant="Main tenant",
            phone_number=f"79 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            email=f"test.{timestamp}.adult1@maildrop.cc",
            street_and_number=f"Randomstrasse {random.randint(1,200)}",
            post_code=postal_code,
            city=city,
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Retired",
            credit_check_type=random.choice(cls.DROPDOWN_OPTIONS['credit_check_type']),
            
            place_of_birth=city,
            place_of_citizenship="Switzerland",
            civil_law_residence=True,
            relocation_last_3_years=random.choice([True, False]),
            community_member=False,
            personal_liability_insurance=True,
            household_insurance=True,

            company_start_date=f"01.{random.randint(1,12):02d}.{random.randint(2018,2023)}",
            employment_terminated=random.choice([True, False]),
            company_street=f"Business Street {random.randint(1,100)}",
            company_postcode=company_postcode,
            company_city=company_city,
            company_contact_person=contact_person,
            company_contact_phone=f"{random.randint(41,81)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
        )
        
        adult2 = PersonData(
            salutation=random.choice(cls.DROPDOWN_OPTIONS['salutation']),
            first_name=random.choice(cls.SWISS_FIRST_NAMES['female']),
            last_name=family_name,
            date_of_birth=f"{random.randint(1,28):02d}.{random.randint(1,12):02d}.{random.randint(1980,1990)}",
            civil_status=adult1.civil_status,
            nationality="Switzerland",
            residency_status=random.choice(cls.DROPDOWN_OPTIONS['residency_status'][:2]),
            type_of_tenant="Spouse, registered partnership",
            phone_number=f"79 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            email=f"test.{timestamp}.adult2@maildrop.cc",
            street_and_number=adult1.street_and_number,
            post_code=postal_code,
            city=city,
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Retired",
            credit_check_type=random.choice(cls.DROPDOWN_OPTIONS['credit_check_type']),
            
            place_of_birth=city,
            place_of_citizenship="Switzerland",
            civil_law_residence=True,
            relocation_last_3_years=random.choice([True, False]),
            community_member=False,
            personal_liability_insurance=True,
            household_insurance=True,

            company_start_date=f"01.{random.randint(1,12):02d}.{random.randint(2018,2023)}",
            employment_terminated=False,
            company_street=f"Office Plaza {random.randint(1,50)}",
            company_postcode=postal_code,
            company_city=city,
            company_contact_person=random.choice(cls.COMPANY_CONTACTS),
            company_contact_phone=f"{random.randint(41,81)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            company_contact_email="hr@company.ch"
        )
        
        child = PersonData(
            salutation=random.choice(["Miss", "Master"]),
            first_name=random.choice(cls.SWISS_FIRST_NAMES['child_female'] + cls.SWISS_FIRST_NAMES['child_male']),
            last_name=family_name,
            date_of_birth=f"{random.randint(1,28):02d}.{random.randint(1,12):02d}.{random.randint(2010,2018)}",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Subtenant",
            phone_number=f"79 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            email=f"test.{timestamp}.child@maildrop.cc",
            street_and_number=adult1.street_and_number,
            post_code=postal_code,
            city=city,
            country="Switzerland",
            move_in_date="01.08.2024",
            
            place_of_birth=city,
            place_of_citizenship="Switzerland",
            civil_law_residence=True
        )
        
        return [adult1, adult2, child]

    @classmethod  
    def create_family_for_test_type(cls, test_type: str = "smoke") -> list:
        """Factory method to create appropriate family data based on test type"""
        test_scenarios = {
            "smoke": "default",
            "regression": "default", 
            "exploratory": "random",
            "validation": "minimal",
            "boundary": "edge_case"
        }
        
        scenario = test_scenarios.get(test_type, "default")
        return cls.create_family_with_child_data(scenario)
    
