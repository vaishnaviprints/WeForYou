from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from models import (
    User, UserCreate, UserLogin, TokenResponse,
    FundCampaign, FundCampaignCreate, CampaignWithStats,
    Donation, DonationCreate, DonationWithReceipt,
    DonationReceipt, Pledge, PledgeCreate, PaymentAttempt,
    DonorStats, VolunteerCreate, VolunteerStats,
    VolunteerCollectionCreate, TermsConditions, TermsCreate,
    generate_volunteer_id
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role
)
from payment_service import PaymentService
from pdf_service import PDFService
from notification_service import NotificationService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
payment_service = PaymentService()
pdf_service = PDFService()
notification_service = NotificationService()

# Create storage directory
storage_path = Path(os.environ.get('LOCAL_STORAGE_PATH', '/app/backend/storage'))
storage_path.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI(title="WeForYou Foundation API - Extended")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        roles=user_data.roles
    )
    
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "roles": user.roles
    })
    
    return TokenResponse(access_token=token, user=user)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user_doc.get('is_active', True):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    if not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    user = User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
    
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "roles": user.roles
    })
    
    return TokenResponse(access_token=token, user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    user_doc = await db.users.find_one({"id": current_user['sub']}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return User(**user_doc)


# ==================== ADMIN - USER MANAGEMENT ====================

@api_router.post("/admin/users/create", response_model=User)
async def admin_create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin creates new user (donor, volunteer, or general user)"""
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        roles=user_data.roles,
        created_by=current_user['sub']
    )
    
    # Generate volunteer ID if volunteer role
    if "volunteer" in user_data.roles:
        user.volunteer_id = generate_volunteer_id()
        user.assigned_by = current_user['sub']
    
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    return user

@api_router.post("/admin/volunteers/create", response_model=User)
async def admin_create_volunteer(
    volunteer_data: VolunteerCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin creates new volunteer with auto-generated ID"""
    existing = await db.users.find_one({"email": volunteer_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    volunteer_id = generate_volunteer_id()
    
    user = User(
        email=volunteer_data.email,
        full_name=volunteer_data.full_name,
        phone=volunteer_data.phone,
        roles=["volunteer", "donor"],
        volunteer_id=volunteer_id,
        assigned_by=current_user['sub'],
        created_by=current_user['sub']
    )
    
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(volunteer_data.password)
    user_dict['address'] = volunteer_data.address
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Send welcome notification
    await notification_service.send_email(
        volunteer_data.email,
        "Welcome to WeForYou Foundation - Volunteer",
        f"Welcome {volunteer_data.full_name}! Your Volunteer ID is: {volunteer_id}. Login credentials sent separately."
    )
    
    return user

@api_router.get("/admin/users")
async def admin_get_all_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all users with optional filters"""
    query = {}
    if role:
        query['roles'] = role
    if is_active is not None:
        query['is_active'] = is_active
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return users

@api_router.patch("/admin/users/{user_id}/toggle-active")
async def admin_toggle_user_status(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Activate or deactivate user"""
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user_doc.get('is_active', True)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": new_status}}
    )
    
    return {"status": "success", "is_active": new_status}

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete user (soft delete - mark as inactive)"""
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user_id == current_user['sub']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "message": "User deactivated"}

@api_router.patch("/admin/users/{user_id}/roles")
async def admin_update_user_roles(
    user_id: str,
    roles: List[str],
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update user roles"""
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate volunteer ID if adding volunteer role
    update_data = {"roles": roles}
    if "volunteer" in roles and not user_doc.get('volunteer_id'):
        update_data['volunteer_id'] = generate_volunteer_id()
        update_data['assigned_by'] = current_user['sub']
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    return {"status": "success", "roles": roles}


# ==================== ADMIN - VOLUNTEER MANAGEMENT ====================

@api_router.get("/admin/volunteers")
async def admin_get_volunteers(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all volunteers with their statistics"""
    volunteers = await db.users.find(
        {"roles": "volunteer"},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    result = []
    for vol in volunteers:
        # Get volunteer stats
        donations = await db.donations.find({"collected_by": vol['volunteer_id']}).to_list(1000)
        
        total_collected = sum(d['amount'] for d in donations if d['status'] in ['success', 'pending_deposit'])
        cash_collected = sum(d['amount'] for d in donations if d['method'] == 'cash' and d['status'] in ['success', 'pending_deposit'])
        online_collected = sum(d['amount'] for d in donations if d['method'] != 'cash' and d['status'] == 'success')
        pending_deposit = sum(d['amount'] for d in donations if d['method'] == 'cash' and d['status'] == 'pending_deposit')
        
        vol['stats'] = {
            'total_collected': total_collected,
            'cash_collected': cash_collected,
            'online_collected': online_collected,
            'pending_deposit': pending_deposit,
            'total_collections': len(donations)
        }
        
        result.append(vol)
    
    return result

@api_router.get("/admin/volunteers/{volunteer_id}/collections")
async def admin_get_volunteer_collections(
    volunteer_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all collections by a volunteer"""
    collections = await db.donations.find(
        {"collected_by": volunteer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for collection in collections:
        if isinstance(collection.get('created_at'), str):
            collection['created_at'] = datetime.fromisoformat(collection['created_at'])
        if isinstance(collection.get('updated_at'), str):
            collection['updated_at'] = datetime.fromisoformat(collection['updated_at'])
    
    return collections

@api_router.post("/admin/volunteers/{volunteer_id}/confirm-deposit/{donation_id}")
async def admin_confirm_cash_deposit(
    volunteer_id: str,
    donation_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin confirms cash deposit from volunteer"""
    donation_doc = await db.donations.find_one({"id": donation_id, "collected_by": volunteer_id})
    if not donation_doc:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    if donation_doc['method'] != 'cash':
        raise HTTPException(status_code=400, detail="Only cash donations can be confirmed")
    
    await db.donations.update_one(
        {"id": donation_id},
        {
            "$set": {
                "status": "success",
                "deposit_confirmed": True,
                "deposit_confirmed_by": current_user['sub'],
                "deposit_confirmed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update campaign totals
    await db.campaigns.update_one(
        {"id": donation_doc['campaign_id']},
        {
            "$inc": {
                "current_amount": donation_doc['amount'],
                "donor_count": 1
            }
        }
    )
    
    # Generate receipt
    await generate_receipt_background(donation_id)
    
    return {"status": "success", "message": "Cash deposit confirmed"}

# ==================== VOLUNTEER - COLLECTION ENDPOINTS ====================

@api_router.post("/volunteer/collect-donation")
async def volunteer_collect_donation(
    collection_data: VolunteerCollectionCreate,
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Volunteer collects donation from general user"""
    # Verify volunteer
    volunteer = await db.users.find_one({"id": current_user['sub'], "roles": "volunteer"})
    if not volunteer:
        raise HTTPException(status_code=403, detail="Only volunteers can collect donations")
    
    volunteer_id = volunteer.get('volunteer_id')
    
    # Verify campaign exists
    campaign = await db.campaigns.find_one({"id": collection_data.campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Create donation record
    donation = Donation(
        campaign_id=collection_data.campaign_id,
        amount=collection_data.amount,
        currency="INR",
        method=collection_data.payment_mode,
        donor_name=collection_data.donor_name,
        donor_phone=collection_data.donor_phone,
        collected_by=volunteer_id,
        want_80g=collection_data.want_80g,
        pan=collection_data.pan,
        address=collection_data.address,
        status="pending" if collection_data.payment_mode == "online" else "pending_deposit"
    )
    
    donation_dict = donation.model_dump()
    donation_dict['created_at'] = donation_dict['created_at'].isoformat()
    donation_dict['updated_at'] = donation_dict['updated_at'].isoformat()
    
    await db.donations.insert_one(donation_dict)
    
    if collection_data.payment_mode == "cash":
        # Send confirmation to donor immediately
        donor_contact = collection_data.donor_phone or collection_data.donor_email
        if donor_contact:
            await notification_service.send_donation_confirmation(
                {**donation_dict, 'campaign_title': campaign['title']},
                donor_contact,
                volunteer['full_name']
            )
        
        # Alert volunteer about cash responsibility
        await notification_service.send_cash_collection_alert(
            volunteer['email'],
            collection_data.amount,
            collection_data.donor_name
        )
        
        # Alert admin
        admin = await db.users.find_one({"roles": "admin"})
        if admin:
            await notification_service.send_admin_cash_alert(
                admin['email'],
                volunteer['full_name'],
                collection_data.amount,
                collection_data.donor_name
            )
        
        return {
            "status": "success",
            "message": "Cash donation collected. Please deposit within 48 hours.",
            "donation_id": donation.id,
            "reminder": "You are responsible for depositing this cash to Foundation account"
        }
    
    else:  # Online payment
        # Create payment order
        order = await payment_service.create_order(
            amount=collection_data.amount,
            currency="INR",
            donation_id=donation.id,
            user_email=collection_data.donor_email or volunteer['email']
        )
        
        # Create payment attempt
        attempt = PaymentAttempt(
            donation_id=donation.id,
            provider_payload=order
        )
        attempt_dict = attempt.model_dump()
        attempt_dict['created_at'] = attempt_dict['created_at'].isoformat()
        await db.payment_attempts.insert_one(attempt_dict)
        
        return {
            "status": "redirect_to_payment",
            "donation_id": donation.id,
            "order": order,
            "razorpay_key": payment_service.razorpay_key_id or "mock_key"
        }

@api_router.get("/volunteer/my-collections")
async def volunteer_get_collections(
    status: Optional[str] = None,
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Get volunteer's collected donations"""
    volunteer = await db.users.find_one({"id": current_user['sub']})
    volunteer_id = volunteer.get('volunteer_id')
    
    query = {"collected_by": volunteer_id}
    if status:
        query['status'] = status
    
    collections = await db.donations.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for collection in collections:
        if isinstance(collection.get('created_at'), str):
            collection['created_at'] = datetime.fromisoformat(collection['created_at'])
        campaign = await db.campaigns.find_one({"id": collection['campaign_id']}, {"_id": 0, "title": 1})
        collection['campaign_title'] = campaign['title'] if campaign else "Unknown"
    
    return collections

@api_router.get("/volunteer/stats")
async def volunteer_get_stats(
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Get volunteer's statistics"""
    volunteer = await db.users.find_one({"id": current_user['sub']})
    volunteer_id = volunteer.get('volunteer_id')
    
    donations = await db.donations.find({"collected_by": volunteer_id}).to_list(1000)
    
    total_collected = sum(d['amount'] for d in donations if d['status'] in ['success', 'pending_deposit'])
    cash_collected = sum(d['amount'] for d in donations if d['method'] == 'cash' and d['status'] in ['success', 'pending_deposit'])
    online_collected = sum(d['amount'] for d in donations if d['method'] != 'cash' and d['status'] == 'success')
    pending_deposit = sum(d['amount'] for d in donations if d['method'] == 'cash' and d['status'] == 'pending_deposit')
    
    return {
        'volunteer_id': volunteer_id,
        'volunteer_name': volunteer['full_name'],
        'total_collected': total_collected,
        'cash_collected': cash_collected,
        'online_collected': online_collected,
        'pending_deposit': pending_deposit,
        'total_collections': len(donations)
    }


# ==================== CAMPAIGN ENDPOINTS ====================

@api_router.post("/campaigns", response_model=FundCampaign)
async def create_campaign(
    campaign_data: FundCampaignCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Create a new fund campaign (Admin only)"""
    campaign = FundCampaign(
        **campaign_data.model_dump(),
        created_by=current_user['sub']
    )
    
    campaign_dict = campaign.model_dump()
    campaign_dict['created_at'] = campaign_dict['created_at'].isoformat()
    if campaign_dict.get('end_date'):
        campaign_dict['end_date'] = campaign_dict['end_date'].isoformat()
    
    await db.campaigns.insert_one(campaign_dict)
    
    return campaign

@api_router.get("/campaigns", response_model=List[FundCampaign])
async def get_campaigns(status: Optional[str] = "active"):
    """Get all campaigns"""
    query = {}
    if status:
        query['status'] = status
    
    campaigns = await db.campaigns.find(query, {"_id": 0}).to_list(100)
    
    for campaign in campaigns:
        if isinstance(campaign.get('created_at'), str):
            campaign['created_at'] = datetime.fromisoformat(campaign['created_at'])
        if campaign.get('end_date') and isinstance(campaign['end_date'], str):
            campaign['end_date'] = datetime.fromisoformat(campaign['end_date'])
    
    return campaigns

@api_router.get("/campaigns/{campaign_id}", response_model=CampaignWithStats)
async def get_campaign(campaign_id: str):
    """Get campaign details with stats"""
    campaign_doc = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign_doc:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if isinstance(campaign_doc.get('created_at'), str):
        campaign_doc['created_at'] = datetime.fromisoformat(campaign_doc['created_at'])
    if campaign_doc.get('end_date') and isinstance(campaign_doc['end_date'], str):
        campaign_doc['end_date'] = datetime.fromisoformat(campaign_doc['end_date'])
    
    donations = await db.donations.find(
        {"campaign_id": campaign_id, "status": "success", "is_anonymous": False},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    recent_donors = []
    for don in donations:
        if don.get('user_id'):
            user_doc = await db.users.find_one({"id": don['user_id']}, {"_id": 0, "full_name": 1})
            if user_doc:
                recent_donors.append({
                    "name": user_doc['full_name'],
                    "amount": don['amount'],
                    "date": don['created_at']
                })
        elif don.get('donor_name'):
            recent_donors.append({
                "name": don['donor_name'],
                "amount": don['amount'],
                "date": don['created_at']
            })
    
    campaign_doc['recent_donors'] = recent_donors
    
    return CampaignWithStats(**campaign_doc)

@api_router.patch("/admin/campaigns/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update campaign status"""
    await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"status": status}}
    )
    return {"status": "success"}

@api_router.delete("/admin/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete campaign"""
    await db.campaigns.delete_one({"id": campaign_id})
    return {"status": "success", "message": "Campaign deleted"}

# ==================== DONATION ENDPOINTS ====================

@api_router.post("/donations", response_model=dict)
async def create_donation(
    donation_data: DonationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new donation (requires login)"""
    campaign = await db.campaigns.find_one({"id": donation_data.campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if donation_data.want_80g:
        if not donation_data.pan or not donation_data.legal_name:
            raise HTTPException(status_code=400, detail="PAN and Legal Name required for 80G receipt")
    
    donation = Donation(
        **donation_data.model_dump(),
        user_id=current_user['sub']
    )
    
    donation_dict = donation.model_dump()
    donation_dict['created_at'] = donation_dict['created_at'].isoformat()
    donation_dict['updated_at'] = donation_dict['updated_at'].isoformat()
    
    await db.donations.insert_one(donation_dict)
    
    user_doc = await db.users.find_one({"id": current_user['sub']})
    order = await payment_service.create_order(
        amount=donation.amount,
        currency=donation.currency,
        donation_id=donation.id,
        user_email=user_doc['email']
    )
    
    attempt = PaymentAttempt(
        donation_id=donation.id,
        provider_payload=order
    )
    attempt_dict = attempt.model_dump()
    attempt_dict['created_at'] = attempt_dict['created_at'].isoformat()
    await db.payment_attempts.insert_one(attempt_dict)
    
    return {
        "donation_id": donation.id,
        "order": order,
        "razorpay_key": payment_service.razorpay_key_id or "mock_key"
    }

@api_router.post("/donations/{donation_id}/verify")
async def verify_donation(
    donation_id: str,
    payment_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Verify and complete donation payment"""
    donation_doc = await db.donations.find_one({"id": donation_id})
    if not donation_doc:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    if donation_doc.get('user_id') and donation_doc['user_id'] != current_user['sub']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    is_valid = await payment_service.verify_payment(
        order_id=payment_data.get('razorpay_order_id', ''),
        payment_id=payment_data.get('razorpay_payment_id', ''),
        signature=payment_data.get('razorpay_signature', '')
    )
    
    if is_valid:
        await db.donations.update_one(
            {"id": donation_id},
            {
                "$set": {
                    "status": "success",
                    "payment_ref": payment_data.get('razorpay_payment_id'),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        await db.campaigns.update_one(
            {"id": donation_doc['campaign_id']},
            {
                "$inc": {
                    "current_amount": donation_doc['amount'],
                    "donor_count": 1
                }
            }
        )
        
        await generate_receipt_background(donation_id)
        
        # Send confirmation
        if donation_doc.get('donor_phone'):
            await notification_service.send_donation_confirmation(
                {**donation_doc, 'campaign_title': 'campaign'},
                donation_doc['donor_phone']
            )
        
        return {"status": "success", "message": "Payment verified and receipt generated"}
    else:
        await db.donations.update_one(
            {"id": donation_id},
            {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        raise HTTPException(status_code=400, detail="Payment verification failed")

async def generate_receipt_background(donation_id: str):
    """Background task to generate receipt"""
    try:
        donation_doc = await db.donations.find_one({"id": donation_id}, {"_id": 0})
        if not donation_doc:
            return
        
        if donation_doc.get('user_id'):
            user_doc = await db.users.find_one({"id": donation_doc['user_id']}, {"_id": 0})
        else:
            user_doc = {
                'full_name': donation_doc.get('donor_name', 'Anonymous'),
                'email': donation_doc.get('donor_email', 'N/A')
            }
        
        campaign_doc = await db.campaigns.find_one({"id": donation_doc['campaign_id']}, {"_id": 0})
        
        receipt_count = await db.receipts.count_documents({}) + 1
        receipt_number = f"WFY{datetime.now().year}{receipt_count:05d}"
        
        created_at = datetime.fromisoformat(donation_doc['created_at'])
        fy = pdf_service.get_financial_year(created_at)
        
        receipt = DonationReceipt(
            donation_id=donation_id,
            receipt_number=receipt_number,
            pdf_url="",
            fy=fy,
            section_80g=donation_doc.get('want_80g', False)
        )
        
        receipt_dict = receipt.model_dump()
        
        pdf_path = await pdf_service.generate_receipt_pdf(
            donation=donation_doc,
            user=user_doc,
            campaign=campaign_doc,
            receipt=receipt_dict
        )
        
        receipt_dict['pdf_url'] = pdf_path
        receipt_dict['issued_at'] = receipt_dict['issued_at'].isoformat()
        
        await db.receipts.insert_one(receipt_dict)
        
        await db.donations.update_one(
            {"id": donation_id},
            {"$set": {"receipt_id": receipt.id}}
        )
        
    except Exception as e:
        logging.error(f"Receipt generation failed for {donation_id}: {str(e)}")

@api_router.get("/donations/my", response_model=List[DonationWithReceipt])
async def get_my_donations(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's donations"""
    query = {"user_id": current_user['sub']}
    if status:
        query['status'] = status
    
    donations = await db.donations.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for don in donations:
        if isinstance(don.get('created_at'), str):
            don['created_at'] = datetime.fromisoformat(don['created_at'])
        if isinstance(don.get('updated_at'), str):
            don['updated_at'] = datetime.fromisoformat(don['updated_at'])
        
        receipt = None
        if don.get('receipt_id'):
            receipt_doc = await db.receipts.find_one({"id": don['receipt_id']}, {"_id": 0})
            if receipt_doc and isinstance(receipt_doc.get('issued_at'), str):
                receipt_doc['issued_at'] = datetime.fromisoformat(receipt_doc['issued_at'])
                receipt = DonationReceipt(**receipt_doc)
        
        campaign = await db.campaigns.find_one({"id": don['campaign_id']}, {"_id": 0, "title": 1})
        don['campaign_title'] = campaign['title'] if campaign else "Unknown"
        don['receipt'] = receipt
        
        result.append(DonationWithReceipt(**don))
    
    return result

@api_router.get("/donations/{donation_id}/receipt")
async def download_receipt(
    donation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download donation receipt PDF"""
    donation_doc = await db.donations.find_one({"id": donation_id})
    if not donation_doc:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    if donation_doc.get('user_id') and donation_doc['user_id'] != current_user['sub']:
        # Check if admin
        if 'admin' not in current_user.get('roles', []):
            raise HTTPException(status_code=403, detail="Access denied")
    
    if not donation_doc.get('receipt_id'):
        raise HTTPException(status_code=404, detail="Receipt not yet generated")
    
    receipt_doc = await db.receipts.find_one({"id": donation_doc['receipt_id']})
    if not receipt_doc:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    file_path = storage_path / receipt_doc['pdf_url']
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Receipt file not found")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/pdf"
    )

