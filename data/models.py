from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum

class ApplicationStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    ERROR = "error"

@dataclass
class ApartmentDetails:
    """Data model for apartment information"""
    rooms: Optional[str] = None
    price: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = None
    full_text: str = ""
    apartment_id: Optional[str] = None

@dataclass
class ParkingRequirements:
    """Parking-related requirements"""
    wants_parking: bool = False
    regular_spaces: int = 0
    small_spaces: int = 0
    large_spaces: int = 0
    electric_spaces: int = 0
    electric_small_spaces: int = 0
    outdoor_spaces: int = 0
    special_spaces: int = 0
    reason: Optional[str] = None

@dataclass
class HouseholdData:
    """Household information data structure"""
    household_type: Optional[str] = None
    has_pets: Optional[bool] = None
    has_music_instruments: Optional[bool] = None
    is_smoker: Optional[bool] = None

    relocation_reason: Optional[str] = None
    desired_move_date: Optional[str] = None
    mailbox_label: Optional[str] = None

    security_deposit_type: Optional[str] = None
    income_rent_ratio: Optional[bool] = None
    iban: Optional[str] = None
    bank_name: Optional[str] = None
    account_owner: Optional[str] = None

    motivation: Optional[str] = None
    participation_ideas: Optional[str] = None
    relation_to_cooperative: Optional[str] = None
    relation_type: Optional[str] = None

    object_found_on: Optional[str] = None
    remarks: Optional[str] = None

@dataclass
class FormData:
    """Complete form data structure"""
    parking: ParkingRequirements = field(default_factory=ParkingRequirements)
    household: HouseholdData = field(default_factory=HouseholdData)
    wants_car_sharing: bool = False
    wants_motorbike_parking: bool = False
    motorbike_spaces: int = 0
    wants_bike_parking: bool = False
    bike_spaces: int = 0
    electric_bike_spaces: int = 0
    wants_additional_room: bool = False
    additional_room_purpose: Optional[str] = None
    additional_room_area: Optional[str] = None
    wants_storage_room: bool = False
    storage_room_purpose: Optional[str] = None
    storage_room_area: Optional[str] = None
    wants_workshop: bool = False
    workshop_purpose: Optional[str] = None
    wants_coworking: bool = False
    wants_home_office: bool = False
    home_office_reason: Optional[str] = None
    needs_obstacle_free: bool = False

@dataclass
class TestResult:
    """Test execution result"""
    success: bool
    error_message: Optional[str] = None
    screenshot_paths: list = field(default_factory=list)
    apartment_details: Optional[ApartmentDetails] = None
    execution_time: Optional[float] = None