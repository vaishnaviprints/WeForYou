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

