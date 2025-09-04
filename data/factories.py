import random
import time
import copy
from dataclasses import replace

from config.test_config import TestConfig
from data.models import FormData, HouseholdData, ParkingRequirements, PersonData

class TestDataFactory:
    """Factory for creating test data scenarios with reusable base objects"""
    
    REQUIRED_FIELDS = [
        'salutation', 'first_name', 'last_name', 'date_of_birth', 'civil_status', 
        'nationality', 'residency_status', 'type_of_tenant', 'phone_number', 
        'email', 'street_and_number', 'post_code', 'city', 'country', 
        'move_in_date', 'employment_status', 'credit_check_type', 
        'company_start_date', 'employment_terminated', 'company_street', 
        'company_postcode', 'company_city', 'company_contact_person',
        'company_contact_phone', 'company_contact_email'
    ]

    COMPANY_NAMES = [
    "Swiss Tech AG", "Alpine Solutions GmbH", "Zurich Consulting Ltd",
    "Basel Innovations SA", "Geneva Finance Group", "Bern Technologies",
    "Lucerne Services AG", "St. Gallen Solutions", "Winterthur Industries"
    ]

    COMPANY_CONTACTS = [
        "HR Manager", "Personnel Director", "Human Resources", 
        "Maria Schneider", "Thomas Mueller", "Anna Weber",
        "Stefan Fischer", "Nicole Graf", "Daniel Keller"
    ]

    DROPDOWN_OPTIONS = {
        'salutation': ['Mr.', 'Mrs.', 'Ms.'],
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

    RELATION_TYPES = [
        "Already living in the neighborhood",
        "Workplace in the neighborhood",
        "Caring for relatives in the neighborhood", 
        "Children school/kindergarten in the neighborhood"
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
    def get_base_valid_adult(cls) -> PersonData:
        """Base template for a valid adult with all required fields"""
        timestamp = int(time.time())
        return PersonData(
            salutation="Mr.",
            first_name="BaseAdult",
            last_name="Template",
            date_of_birth="15.06.1985",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Main tenant",
            phone_number="79 123 45 67",
            email=f"base.adult.{timestamp}@maildrop.cc",
            street_and_number="Basestrasse 123",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Retired",
            credit_check_type="CreditTrust certificate",

            place_of_birth="Zurich",
            place_of_citizenship="Switzerland",
            current_rental_situation="Tenancy",
            civil_law_residence=True,
            relocation_last_3_years=False,
            community_member=False,
            education="Tertiary level",
            gross_annual_income="CHF 60'000 - CHF 80'000",
            annual_taxable_income="70000",
            personal_liability_insurance=True,
            household_insurance=True,

            company_start_date="01.06.2020",
            employment_terminated=False,
            company_name="Swiss Tech AG",
            company_street="Business Street 50",
            company_postcode="8002",
            company_city="Zurich",
            company_contact_person="HR Manager",
            company_contact_phone="44 987 65 43",
            company_contact_email="hr@swisstech.ch"
        )
    
    @classmethod
    def get_base_valid_child(cls) -> PersonData:
        """Base template for a valid child with required fields"""
        timestamp = int(time.time())
        return PersonData(
            salutation="Ms.",
            first_name="BaseChild",
            last_name="Template",
            date_of_birth="10.09.2015",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Subtenant",
            phone_number="79 555 66 77",
            email=f"base.child.{timestamp}@maildrop.cc",
            street_and_number="Basestrasse 123",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            
            place_of_birth="Zurich",
            civil_law_residence=True
        )
    
    @classmethod
    def make_invalid_postal_code(cls, person: PersonData) -> PersonData:
        """Create copy with invalid postal code"""
        return replace(person, 
            post_code="99999",
            city="InvalidCity"
        )
    
    @classmethod
    def make_invalid_email(cls, person: PersonData) -> PersonData:
        """Create copy with invalid email"""
        return replace(person, email="invalid-email-format")
    
    @classmethod
    def make_invalid_phone(cls, person: PersonData) -> PersonData:
        """Create copy with invalid phone number"""
        return replace(person, phone_number="123")
    
    @classmethod
    def make_missing_required_field(cls, person: PersonData, field_name: str) -> PersonData:
        """Create copy with specific required field missing"""
        return replace(person, **{field_name: None})
    
    @classmethod
    def make_future_birth_date(cls, person: PersonData) -> PersonData:
        """Create copy with future birth date (invalid)"""
        return replace(person, date_of_birth="01.01.2030")
    
    @classmethod
    def make_invalid_employment_combo(cls, person: PersonData) -> PersonData:
        """Create copy with invalid employment combination"""
        return replace(person, 
            date_of_birth="10.09.2015", 
            employment_status="Full-time (90-100%)" 
        )
    
    @classmethod
    def customize_person(cls, base_person: PersonData, **kwargs) -> PersonData:
        """Create copy with custom field values"""
        return replace(base_person, **kwargs)
    
    
    @classmethod
    def create_base_family(cls) -> list:
        """Create base family that can be reused and modified"""
        adult1 = cls.get_base_valid_adult()
        adult2 = cls.get_base_valid_adult()
        child = cls.get_base_valid_child()

        adult1 = cls.customize_person(adult1,
            first_name="John",
            last_name="BaseFamily",
            civil_status="Married",
            type_of_tenant="Main tenant"
        )
        
        adult2 = cls.customize_person(adult2,
            first_name="Sarah",
            last_name="BaseFamily", 
            civil_status="Married",
            type_of_tenant="Spouse, registered partnership",
            salutation="Mrs.",
            employment_status="Part-time (70-89%)"
        )
        
        child = cls.customize_person(child,
            first_name="Emma",
            last_name="BaseFamily"
        )
        
        return [adult1, adult2, child]
    
    @classmethod
    def create_family_with_invalid_postal_codes(cls) -> list:
        """Create family with invalid postal codes for validation testing"""
        base_family = cls.create_base_family()
        
        return [
            cls.make_invalid_postal_code(base_family[0]),
            cls.make_invalid_postal_code(base_family[1]),
            cls.make_invalid_postal_code(base_family[2])
        ]
    
    @classmethod
    def create_family_with_mixed_validity(cls) -> list:
        """Create family with mix of valid and invalid data"""
        base_family = cls.create_base_family()
        
        return [
            base_family[0],
            cls.make_invalid_email(base_family[1]),
            cls.make_invalid_phone(base_family[2])
        ]
    
    @classmethod
    def create_family_missing_required_fields(cls) -> list:
        """Create family with missing required fields"""
        base_family = cls.create_base_family()
        
        return [
            cls.make_missing_required_field(base_family[0], "employment_status"),
            cls.make_missing_required_field(base_family[1], "nationality"),
            cls.make_missing_required_field(base_family[2], "date_of_birth")
        ]

    
    @classmethod
    def create_family_for_validation_test(cls, validation_type: str) -> list:
        """Create family data for specific validation scenarios"""
        validation_scenarios = {
            "valid": cls.create_base_family,
            "invalid_postal": cls.create_family_with_invalid_postal_codes,
            "invalid_email": lambda: [cls.make_invalid_email(p) for p in cls.create_base_family()],
            "invalid_phone": lambda: [cls.make_invalid_phone(p) for p in cls.create_base_family()],
            "missing_required": cls.create_family_missing_required_fields,
            "future_dates": lambda: [cls.make_future_birth_date(p) for p in cls.create_base_family()],
            "mixed_validity": cls.create_family_with_mixed_validity
        }
        
        scenario_func = validation_scenarios.get(validation_type, cls.create_base_family)
        return scenario_func()

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
    def create_minimal_applicant(cls) -> FormData:
        """Applicant with no special requirements"""
        return FormData(household=HouseholdData())

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
        
        household = HouseholdData(
            household_type="Family with children",
            has_pets=True,
            has_music_instruments=True,
            is_smoker=False,
            relocation_reason="Family expansion",
            desired_move_date="01.06.2024",
            mailbox_label="Smith Family",
            security_deposit_type="deposit",
            income_rent_ratio=True,
            iban="CH93 0076 2011 6238 5295 7",
            bank_name="UBS Switzerland",
            account_owner="John Smith",
            motivation="Looking for a community-oriented living space",
            participation_ideas="Interested in community garden and events",
            relation_to_cooperative="New to cooperative",
            object_found_on="Website",
            remarks="Excited to be part of the community!"
        )
        return FormData(
            parking=parking,
            household=household,
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
        
        return FormData(parking=parking, household=HouseholdData())

    @classmethod
    def create_family_with_child_data(cls, scenario: str = "default") -> list:
        """Create data for 2 adults and 1 child with different scenarios"""
        
        if scenario == "minimal":
            return cls._create_minimal_family()
        elif scenario == "edge_case":
            return cls._create_edge_case_family()
        elif scenario == "random":
            return cls._create_random_family()
        elif scenario == "base":
            return cls.create_base_family()
        else:
            return cls._create_default_family()

    @classmethod
    def _create_default_family(cls) -> list:
        """Predictable data for smoke tests and admin verification"""
        timestamp = int(time.time())
        
        adult1 = PersonData(
            salutation="Mr.",
            first_name="John",
            last_name="Test",
            date_of_birth="15.06.1985",
            civil_status="Married",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Main tenant",
            phone_number="79 123 45 67",
            email=f"john.testfamily.{timestamp}@maildrop.cc",
            street_and_number="Teststrasse 123",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Retired",
            credit_check_type="CreditTrust certificate",
            
            place_of_birth="Zurich",
            place_of_citizenship="Switzerland",
            current_rental_situation="Tenancy",
            civil_law_residence=True,
            relocation_last_3_years=False,
            community_member=False,
            education="Tertiary level",
            gross_annual_income="CHF 60'000 - CHF 80'000",
            annual_taxable_income="70000",
            personal_liability_insurance=True,
            household_insurance=True,

            company_start_date="15.03.2019",
            employment_terminated=False,
            company_name="Zurich Consulting Ltd",
            company_street="Corporate Avenue 75",
            company_postcode="8003",
            company_city="Zurich",
            company_contact_person="Maria Schneider",
            company_contact_phone="44 321 54 76",
            company_contact_email="maria.schneider@zurichconsulting.ch"
        )
        
        adult2 = PersonData(
            salutation="Ms.",
            first_name="Sarah",
            last_name="Test",
            date_of_birth="22.03.1987",
            civil_status="Married",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Spouse, registered partnership",
            phone_number="79 987 65 43",
            email=f"sarah.testfamily.{timestamp}@maildrop.cc",
            street_and_number="Teststrasse 123",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Retired",
            credit_check_type="CreditTrust certificate",
            
            place_of_birth="Basel",
            place_of_citizenship="Switzerland",
            current_rental_situation="Tenancy",
            civil_law_residence=True,
            relocation_last_3_years=False,
            community_member=False,
            education="Secondary level II",
            gross_annual_income="CHF 40'000 - CHF 50'000",
            annual_taxable_income="45000",
            personal_liability_insurance=True,
            household_insurance=True,

            company_start_date="01.09.2021",
            employment_terminated=False,
            company_name="Basel Innovations SA",
            company_street="Innovation Park 25",
            company_postcode="4002",
            company_city="Basel",
            company_contact_person="Thomas Mueller",
            company_contact_phone="61 456 78 90",
            company_contact_email="thomas.mueller@baselinnovations.ch"
        )
        
        child = PersonData(
            salutation="Miss",
            first_name="Emma",
            last_name="Test",
            date_of_birth="10.09.2015",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Subtenant",
            phone_number="79 555 66 77",
            email=f"emma.testfamily.{timestamp}@maildrop.cc",
            street_and_number="Teststrasse 123",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            
            place_of_birth="Zurich",
            place_of_citizenship="Switzerland",
            current_rental_situation="Living with parents",
            civil_law_residence=True
        )
        
        return [adult1, adult2, child]

    @classmethod 
    def _create_random_family(cls) -> list:
        """Generate realistic random family data"""
        timestamp = int(time.time())
        family_name = random.choice(cls.SWISS_SURNAMES)
        city, postal_code = random.choice(cls.SWISS_CITIES)
        
        company_city, company_postcode = random.choice(cls.SWISS_CITIES)
        company_name = random.choice(cls.COMPANY_NAMES)
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
            employment_status=random.choice(cls.DROPDOWN_OPTIONS['employment_status']),
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
            company_name=company_name,
            company_street=f"Business Street {random.randint(1,100)}",
            company_postcode=company_postcode,
            company_city=company_city,
            company_contact_person=contact_person,
            company_contact_phone=f"{random.randint(41,81)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            company_contact_email=f"hr@{company_name.lower().replace(' ', '').replace('ag', '').replace('gmbh', '').replace('sa', '').replace('ltd', '')}.ch"
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
            employment_status=random.choice(cls.DROPDOWN_OPTIONS['employment_status']),
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
            company_name=random.choice(cls.COMPANY_NAMES),
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
    def _create_minimal_family(cls) -> list:
        """Minimal required fields only - test form validation"""
        timestamp = int(time.time())
        
        adult1 = PersonData(
            salutation="Mr.",
            first_name="MinTest",
            last_name="Family",
            date_of_birth="15.06.1985",
            civil_status="Single",
            nationality="Switzerland", 
            residency_status="(C) Long-term resident",
            type_of_tenant="Main tenant",
            phone_number="79 123 45 67",
            email=f"minimal.test.{timestamp}@maildrop.cc",
            street_and_number="Minimalstrasse 1",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Full-time (90-100%)",
            credit_check_type="CreditTrust certificate"
        )
        
        adult2 = PersonData(
            salutation="Mrs.",
            first_name="MinTest2",
            last_name="Family",
            date_of_birth="22.03.1987",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Roommate, life partner",
            phone_number="79 987 65 43",
            email=f"minimal.test2.{timestamp}@maildrop.cc",
            street_and_number="Minimalstrasse 1",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024",
            employment_status="Part-time (70-89%)",
            credit_check_type="CreditTrust certificate"
        )
        
        child = PersonData(
            salutation="Miss",
            first_name="MinChild",
            last_name="Family",
            date_of_birth="10.09.2015",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Subtenant",
            phone_number="79 555 66 77",
            email=f"minimal.child.{timestamp}@maildrop.cc",
            street_and_number="Minimalstrasse 1",
            post_code="8001",
            city="Zurich",
            country="Switzerland",
            move_in_date="01.08.2024"
        )
        
        return [adult1, adult2, child]

    @classmethod
    def _create_edge_case_family(cls) -> list:
        """Test edge cases and special characters"""
        timestamp = int(time.time())
        
        adult1 = PersonData(
            salutation="Mr.",
            first_name="Jean-François",
            last_name="Müller-Schmidt",
            date_of_birth="01.01.1980",
            civil_status="Divorced",
            nationality="Switzerland",
            residency_status="(G) Frontier worker",
            type_of_tenant="Main tenant", 
            phone_number="79 000 00 01",
            email=f"edge.case.test.{timestamp}@maildrop.cc",
            street_and_number="Längste-Strassennamen-In-Der-Schweiz 999",
            post_code="9999",
            city="Appenzell",
            country="Switzerland",
            move_in_date="31.12.2024",
            employment_status="Self-employed",
            credit_check_type="Excerpt from debt collection"
        )
        
        adult2 = PersonData(
            salutation="Ms.",
            first_name="María-José",
            last_name="Müller-Schmidt",
            date_of_birth="29.02.1984",
            civil_status="Separated",
            nationality="Switzerland",
            residency_status="(L) Short-stay resident",
            type_of_tenant="Roommate, life partner",
            phone_number="79 999 99 99",
            email=f"edge.case.test2.{timestamp}@maildrop.cc",
            street_and_number="Längste-Strassennamen-In-Der-Schweiz 999",
            post_code="9999",
            city="Appenzell",
            country="Switzerland",
            move_in_date="31.12.2024",
            employment_status="Part-time (less than 50%)",
            credit_check_type="Excerpt from debt collection"
        )
        
        child = PersonData(
            salutation="Master",
            first_name="José-María",
            last_name="Müller-Schmidt",
            date_of_birth="31.12.2018",
            civil_status="Single",
            nationality="Switzerland",
            residency_status="(C) Long-term resident",
            type_of_tenant="Subtenant",
            phone_number="79 111 11 11",
            email=f"edge.case.child.{timestamp}@maildrop.cc",
            street_and_number="Längste-Strassennamen-In-Der-Schweiz 999",
            post_code="9999",
            city="Appenzell",
            country="Switzerland",
            move_in_date="31.12.2024"
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
    
    @classmethod
    def generate_realistic_employment_data(cls, base_person: PersonData) -> dict:
        """Generate realistic employment data based on person's location"""
        company_cities = [base_person.city, "Zurich", "Basel", "Geneva"]
        company_city = random.choice(company_cities)
        company_postcode = next((pc for city, pc in cls.SWISS_CITIES if city == company_city), "8001")
        
        return {
            "company_start_date": f"01.{random.randint(1,12):02d}.{random.randint(2018,2023)}",
            "employment_terminated": False,
            "company_name": random.choice(cls.COMPANY_NAMES),
            "company_street": f"Business Avenue {random.randint(1,99)}",
            "company_postcode": company_postcode,
            "company_city": company_city,
            "company_contact_person": random.choice(cls.COMPANY_CONTACTS),
            "company_contact_phone": f"{random.randint(41,81)} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
            "company_contact_email": "hr@company.ch"
        }