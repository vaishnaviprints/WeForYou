"""
Delta models - Additional models for new features
Import these in server.py alongside existing models
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone
import uuid

# ==================== MEMBER MODELS ====================

class MemberBase(BaseModel):
    full_name: str
    phone: str
    email: Optional[EmailStr] = None
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pan: Optional[str] = None
    consent_public_donor: bool = False
    consent_marketing: bool = False

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str  # volunteer or admin user_id
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== BLOOD DONOR MODELS ====================

class BloodDonorBase(BaseModel):
    member_id: Optional[str] = None  # If registering a member
    user_id: Optional[str] = None  # If self-registration
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    phone: str
    email: Optional[EmailStr] = None
    full_name: str
    age: int
    weight: float  # in kg
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    availability: bool = True
    last_donation_date: Optional[str] = None

class BloodDonorCreate(BloodDonorBase):
    consent_public: bool  # Mandatory consent

class BloodDonor(BloodDonorBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consent_public: bool = False
    consent_public_at: Optional[datetime] = None
    moderation_hidden: bool = False
    contact_reveal_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== EVENT MODELS ====================

class EventBase(BaseModel):
    title: str
    description: str
    schedule_start: datetime
    schedule_end: Optional[datetime] = None
    venue: Optional[str] = None
    capacity: Optional[int] = None
    fee_enabled: bool = False
    fee_amount: Optional[float] = None
    image_url: Optional[str] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    status: Literal["DRAFT", "LIVE", "PAUSED", "COMPLETED", "ARCHIVED"] = "DRAFT"
    registered_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventRegistration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    user_id: str
    payment_required: bool
    payment_status: Optional[Literal["PENDING", "PAID", "FAILED"]] = None
    donation_id: Optional[str] = None  # Link to donation if paid
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== VOLUNTEER ACTIVITY MODELS ====================

class VolunteerActivityBase(BaseModel):
    activity_type: str  # e.g., "Field Visit", "Donation Collection", "Event Support"
    activity_date: str
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    photos: List[str] = []

class VolunteerActivityCreate(VolunteerActivityBase):
    pass

class VolunteerActivity(VolunteerActivityBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    volunteer_id: str
    approved_by: Optional[str] = None
    status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== CERTIFICATE MODELS ====================

class Certificate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    volunteer_id: str
    certificate_type: str  # e.g., "Volunteer of the Month", "100 Hours Service"
    serial_number: str
    issued_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    issued_by: str  # Admin user_id
    pdf_url: str
    qr_verify_url: str
    revoked: bool = False

# ==================== SPONSOR & BANNER MODELS ====================

class SponsorBase(BaseModel):
    name: str
    logo_url: str
    website_url: Optional[str] = None
    description: Optional[str] = None
    active_from: Optional[datetime] = None
    active_until: Optional[datetime] = None

class SponsorCreate(SponsorBase):
    pass

class Sponsor(SponsorBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    impression_count: int = 0
    click_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BannerBase(BaseModel):
    title: str
    image_url: str
    link_url: Optional[str] = None
    placement: Literal["home", "campaigns", "events", "all"]
    active_from: Optional[datetime] = None
    active_until: Optional[datetime] = None

class BannerCreate(BannerBase):
    pass

class Banner(BannerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    impression_count: int = 0
    click_count: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Update existing Donation model to support new types
class DonationType:
    CAMPAIGN = "CAMPAIGN"
    GENERAL = "GENERAL"
    EVENT_FEE = "EVENT_FEE"
    ON_BEHALF = "ON_BEHALF"  # Collected by volunteer
    VOLUNTEER_OWN = "VOLUNTEER_OWN"  # Volunteer's own donation
