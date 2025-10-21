from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone
import uuid

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

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
    method: Optional[Literal["upi", "card", "netbanking"]] = None
    # 80G Fields
    want_80g: bool = False
    pan: Optional[str] = None
    legal_name: Optional[str] = None
    address: Optional[str] = None

class DonationCreate(DonationBase):
    pass

class Donation(DonationBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: Literal["pending", "success", "failed", "refunded"] = "pending"
    payment_provider: str = "razorpay"
    payment_ref: Optional[str] = None
    receipt_id: Optional[str] = None
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
    fy: str  # e.g., "2024-25"
    section_80g: bool = False
    ack_no: Optional[str] = None

# Pledge Models (Recurring)
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

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class DonationWithReceipt(Donation):
    receipt: Optional[DonationReceipt] = None
    campaign_title: Optional[str] = None

class CampaignWithStats(FundCampaign):
    total_donations: int = 0
    recent_donors: List[dict] = []

class DonorStats(BaseModel):
    total_donated: float
    donation_count: int
    first_donation: Optional[datetime] = None
    last_donation: Optional[datetime] = None