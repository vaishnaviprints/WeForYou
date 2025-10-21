from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone
import uuid
import random
import string

# User Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str
    roles: List[Literal["admin", "volunteer", "donor"]] = Field(default=["donor"])

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    roles: List[str] = Field(default=["donor"])
    volunteer_id: Optional[str] = None  # Only for volunteers
    assigned_by: Optional[str] = None  # Admin who created volunteer
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None  # Admin who created this user

# Volunteer-specific Models
class VolunteerCreate(BaseModel):
    email: EmailStr
    full_name: str
    phone: str
    password: str
    address: Optional[str] = None

class VolunteerStats(BaseModel):
    total_collected: float = 0.0
    cash_collected: float = 0.0
    online_collected: float = 0.0
    pending_deposit: float = 0.0
    total_collections: int = 0

# FundCampaign Models
class FundCampaignBase(BaseModel):
    title: str
    description: str
    goal_amount: float
    currency: str = "INR"
    allow_recurring: bool = False
    image_url: Optional[str] = None
    end_date: Optional[datetime] = None

class FundCampaignCreate(FundCampaignBase):
    pass

class FundCampaign(FundCampaignBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    current_amount: float = 0.0
    donor_count: int = 0
    status: Literal["active", "completed", "paused"] = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Donation Models
class DonationBase(BaseModel):
    campaign_id: str
    amount: float
    currency: str = "INR"
    is_anonymous: bool = False
    method: Optional[Literal["upi", "card", "netbanking", "cash"]] = None
    # 80G Fields
    want_80g: bool = False
    pan: Optional[str] = None
    legal_name: Optional[str] = None
    address: Optional[str] = None

class DonationCreate(DonationBase):
    pass

# Volunteer Collection Model
class VolunteerCollectionCreate(BaseModel):
    campaign_id: str
    donor_name: str
    donor_phone: str
    donor_email: Optional[EmailStr] = None
    amount: float
    payment_mode: Literal["cash", "online"]
    want_80g: bool = False
    pan: Optional[str] = None
    address: Optional[str] = None

class Donation(DonationBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Can be null for volunteer collections
    donor_name: Optional[str] = None  # For volunteer collections
    donor_phone: Optional[str] = None  # For volunteer collections
    collected_by: Optional[str] = None  # Volunteer ID if collected by volunteer
    status: Literal["pending", "success", "failed", "refunded", "pending_deposit"] = "pending"
    payment_provider: str = "razorpay"
    payment_ref: Optional[str] = None
    receipt_id: Optional[str] = None
    deposit_confirmed: bool = False  # For cash collections
    deposit_confirmed_by: Optional[str] = None  # Admin who confirmed
    deposit_confirmed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# DonationReceipt Models
class DonationReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    donation_id: str
    receipt_number: str
    pdf_url: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fy: str
    section_80g: bool = False
    ack_no: Optional[str] = None

# Pledge Models
class PledgeBase(BaseModel):
    campaign_id: str
    amount: float
    frequency: Literal["monthly"] = "monthly"

class PledgeCreate(PledgeBase):
    pass

class Pledge(PledgeBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mandate_ref: Optional[str] = None
    status: Literal["active", "paused", "cancelled"] = "active"
    next_charge_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# PaymentAttempt Models
class PaymentAttempt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    donation_id: Optional[str] = None
    pledge_id: Optional[str] = None
    attempt_no: int = 1
    status: Literal["initiated", "success", "failed"] = "initiated"
    provider_payload: dict = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Terms & Conditions Model
class TermsConditions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    version: str
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TermsCreate(BaseModel):
    title: str
    content: str
    version: str

# Notification Model (for tracking)
class NotificationLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipient: str  # Email or phone
    type: Literal["email", "sms"]
    subject: Optional[str] = None
    message: str
    status: Literal["sent", "failed", "mocked"] = "mocked"
    related_to: Optional[str] = None  # donation_id, user_id, etc
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class DonationWithReceipt(Donation):
    receipt: Optional[DonationReceipt] = None
    campaign_title: Optional[str] = None
    volunteer_name: Optional[str] = None

class CampaignWithStats(FundCampaign):
    total_donations: int = 0
    recent_donors: List[dict] = []

class DonorStats(BaseModel):
    total_donated: float
    donation_count: int
    first_donation: Optional[datetime] = None
    last_donation: Optional[datetime] = None

def generate_volunteer_id() -> str:
    """Generate unique volunteer ID like VL-2024-XXXX"""
    year = datetime.now().year
    random_num = ''.join(random.choices(string.digits, k=4))
    return f"VL-{year}-{random_num}"