from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile, BackgroundTasks
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
import uuid

from models import (
    User, UserCreate, UserLogin, TokenResponse,
    FundCampaign, FundCampaignCreate, CampaignWithStats,
    Donation, DonationCreate, DonationWithReceipt,
    DonationReceipt, Pledge, PledgeCreate, PaymentAttempt,
    DonorStats
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role
)
from payment_service import PaymentService
from pdf_service_mock import PDFService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
payment_service = PaymentService()
pdf_service = PDFService()

# Create storage directory
storage_path = Path(os.environ.get('LOCAL_STORAGE_PATH', '/app/backend/storage'))
storage_path.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI(title="WeForYou Foundation API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        roles=user_data.roles
    )
    
    # Hash password and store
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Generate token
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
    
    if not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Convert to User model
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    user = User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
    
    # Generate token
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
    
    # Convert dates
    if isinstance(campaign_doc.get('created_at'), str):
        campaign_doc['created_at'] = datetime.fromisoformat(campaign_doc['created_at'])
    if campaign_doc.get('end_date') and isinstance(campaign_doc['end_date'], str):
        campaign_doc['end_date'] = datetime.fromisoformat(campaign_doc['end_date'])
    
    # Get recent donors (non-anonymous)
    donations = await db.donations.find(
        {"campaign_id": campaign_id, "status": "success", "is_anonymous": False},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    recent_donors = []
    for don in donations:
        user_doc = await db.users.find_one({"id": don['user_id']}, {"_id": 0, "full_name": 1})
        if user_doc:
            recent_donors.append({
                "name": user_doc['full_name'],
                "amount": don['amount'],
                "date": don['created_at']
            })
    
    campaign_doc['recent_donors'] = recent_donors
    
    return CampaignWithStats(**campaign_doc)

# ==================== DONATION ENDPOINTS ====================

@api_router.post("/donations", response_model=dict)
async def create_donation(
    donation_data: DonationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new donation (requires login)"""
    # Verify campaign exists
    campaign = await db.campaigns.find_one({"id": donation_data.campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Validate 80G fields
    if donation_data.want_80g:
        if not donation_data.pan or not donation_data.legal_name:
            raise HTTPException(status_code=400, detail="PAN and Legal Name required for 80G receipt")
    
    # Create donation
    donation = Donation(
        **donation_data.model_dump(),
        user_id=current_user['sub']
    )
    
    donation_dict = donation.model_dump()
    donation_dict['created_at'] = donation_dict['created_at'].isoformat()
    donation_dict['updated_at'] = donation_dict['updated_at'].isoformat()
    
    await db.donations.insert_one(donation_dict)
    
    # Create payment order
    user_doc = await db.users.find_one({"id": current_user['sub']})
    order = await payment_service.create_order(
        amount=donation.amount,
        currency=donation.currency,
        donation_id=donation.id,
        user_email=user_doc['email']
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
    
    if donation_doc['user_id'] != current_user['sub']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify payment
    is_valid = await payment_service.verify_payment(
        order_id=payment_data.get('razorpay_order_id', ''),
        payment_id=payment_data.get('razorpay_payment_id', ''),
        signature=payment_data.get('razorpay_signature', '')
    )
    
    if is_valid:
        # Update donation status
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
        
        user_doc = await db.users.find_one({"id": donation_doc['user_id']}, {"_id": 0})
        campaign_doc = await db.campaigns.find_one({"id": donation_doc['campaign_id']}, {"_id": 0})
        
        # Generate receipt number
        receipt_count = await db.receipts.count_documents({}) + 1
        receipt_number = f"WFY{datetime.now().year}{receipt_count:05d}"
        
        # Get FY
        created_at = datetime.fromisoformat(donation_doc['created_at'])
        fy = pdf_service.get_financial_year(created_at)
        
        receipt = DonationReceipt(
            donation_id=donation_id,
            receipt_number=receipt_number,
            pdf_url="",  # Will be updated
            fy=fy,
            section_80g=donation_doc.get('want_80g', False)
        )
        
        receipt_dict = receipt.model_dump()
        
        # Generate PDF
        pdf_path = await pdf_service.generate_receipt_pdf(
            donation=donation_doc,
            user=user_doc,
            campaign=campaign_doc,
            receipt=receipt_dict
        )
        
        receipt_dict['pdf_url'] = pdf_path
        receipt_dict['issued_at'] = receipt_dict['issued_at'].isoformat()
        
        # Save receipt
        await db.receipts.insert_one(receipt_dict)
        
        # Update donation with receipt ID
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
        
        # Get receipt
        receipt = None
        if don.get('receipt_id'):
            receipt_doc = await db.receipts.find_one({"id": don['receipt_id']}, {"_id": 0})
            if receipt_doc and isinstance(receipt_doc.get('issued_at'), str):
                receipt_doc['issued_at'] = datetime.fromisoformat(receipt_doc['issued_at'])
                receipt = DonationReceipt(**receipt_doc)
        
        # Get campaign title
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
    
    if donation_doc['user_id'] != current_user['sub']:
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

# ==================== PLEDGE ENDPOINTS ====================

@api_router.post("/pledges", response_model=Pledge)
async def create_pledge(
    pledge_data: PledgeCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a recurring pledge"""
    campaign = await db.campaigns.find_one({"id": pledge_data.campaign_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if not campaign.get('allow_recurring', False):
        raise HTTPException(status_code=400, detail="This campaign does not support recurring donations")
    
    pledge = Pledge(
        **pledge_data.model_dump(),
        user_id=current_user['sub'],
        next_charge_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    
    pledge_dict = pledge.model_dump()
    pledge_dict['created_at'] = pledge_dict['created_at'].isoformat()
    if pledge_dict.get('next_charge_at'):
        pledge_dict['next_charge_at'] = pledge_dict['next_charge_at'].isoformat()
    
    await db.pledges.insert_one(pledge_dict)
    
    return pledge

@api_router.get("/pledges/my", response_model=List[Pledge])
async def get_my_pledges(current_user: dict = Depends(get_current_user)):
    """Get current user's pledges"""
    pledges = await db.pledges.find(
        {"user_id": current_user['sub']},
        {"_id": 0}
    ).to_list(100)
    
    for pledge in pledges:
        if isinstance(pledge.get('created_at'), str):
            pledge['created_at'] = datetime.fromisoformat(pledge['created_at'])
        if pledge.get('next_charge_at') and isinstance(pledge['next_charge_at'], str):
            pledge['next_charge_at'] = datetime.fromisoformat(pledge['next_charge_at'])
    
    return pledges

@api_router.patch("/pledges/{pledge_id}")
async def update_pledge(
    pledge_id: str,
    action: str,
    current_user: dict = Depends(get_current_user)
):
    """Update pledge status (pause/cancel)"""
    pledge_doc = await db.pledges.find_one({"id": pledge_id})
    if not pledge_doc:
        raise HTTPException(status_code=404, detail="Pledge not found")
    
    if pledge_doc['user_id'] != current_user['sub']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if action not in ["pause", "cancel", "activate"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    status_map = {"pause": "paused", "cancel": "cancelled", "activate": "active"}
    
    await db.pledges.update_one(
        {"id": pledge_id},
        {"$set": {"status": status_map[action]}}
    )
    
    return {"status": "success", "message": f"Pledge {action}d successfully"}

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get campaign analytics (Admin only)"""
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Aggregate donations
    pipeline = [
        {"$match": {"campaign_id": campaign_id, "status": "success"}},
        {"$group": {
            "_id": None,
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1},
            "avg_amount": {"$avg": "$amount"}
        }}
    ]
    
    result = await db.donations.aggregate(pipeline).to_list(1)
    stats = result[0] if result else {"total_amount": 0, "count": 0, "avg_amount": 0}
    
    # Top donors (non-anonymous)
    top_donors_pipeline = [
        {"$match": {"campaign_id": campaign_id, "status": "success", "is_anonymous": False}},
        {"$group": {
            "_id": "$user_id",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]
    
    top_donors_raw = await db.donations.aggregate(top_donors_pipeline).to_list(10)
    top_donors = []
    for donor in top_donors_raw:
        user = await db.users.find_one({"id": donor['_id']}, {"_id": 0, "full_name": 1, "email": 1})
        if user:
            top_donors.append({
                "name": user['full_name'],
                "email": user['email'],
                "total_donated": donor['total'],
                "donation_count": donor['count']
            })
    
    return {
        "campaign": campaign,
        "stats": stats,
        "top_donors": top_donors
    }

@api_router.get("/admin/donors")
async def get_donor_directory(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get donor directory (Admin only)"""
    # Find all users with successful donations
    donors_pipeline = [
        {"$match": {"status": "success"}},
        {"$group": {
            "_id": "$user_id",
            "total_donated": {"$sum": "$amount"},
            "donation_count": {"$sum": 1},
            "first_donation": {"$min": "$created_at"},
            "last_donation": {"$max": "$created_at"}
        }}
    ]
    
    donors_stats = await db.donations.aggregate(donors_pipeline).to_list(1000)
    
    result = []
    for stats in donors_stats:
        user = await db.users.find_one({"id": stats['_id']}, {"_id": 0, "password_hash": 0})
        if user:
            result.append({
                "user": user,
                "stats": {
                    "total_donated": stats['total_donated'],
                    "donation_count": stats['donation_count'],
                    "first_donation": stats['first_donation'],
                    "last_donation": stats['last_donation']
                }
            })
    
    return result

@api_router.post("/admin/donations/{donation_id}/refund")
async def refund_donation(
    donation_id: str,
    refund_data: dict,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Refund a donation (Admin only)"""
    donation_doc = await db.donations.find_one({"id": donation_id})
    if not donation_doc:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    if donation_doc['status'] != 'success':
        raise HTTPException(status_code=400, detail="Only successful donations can be refunded")
    
    # Process refund
    refund = await payment_service.refund_payment(
        payment_id=donation_doc['payment_ref'],
        amount=refund_data.get('amount')  # None = full refund
    )
    
    # Update donation
    await db.donations.update_one(
        {"id": donation_id},
        {
            "$set": {
                "status": "refunded",
                "refund_ref": refund['id'],
                "refund_note": refund_data.get('note', ''),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Update campaign totals
    refund_amount = refund_data.get('amount', donation_doc['amount'])
    await db.campaigns.update_one(
        {"id": donation_doc['campaign_id']},
        {
            "$inc": {
                "current_amount": -refund_amount
            }
        }
    )
    
    return {"status": "success", "refund": refund}

# ==================== WEBHOOK ENDPOINTS ====================

@api_router.post("/webhooks/razorpay")
async def razorpay_webhook(payload: dict):
    """Handle Razorpay webhooks (idempotent)"""
    event = payload.get('event')
    
    if event == 'payment.captured':
        payment = payload.get('payload', {}).get('payment', {}).get('entity', {})
        order_id = payment.get('order_id')
        payment_id = payment.get('id')
        
        # Find donation by order_id
        attempt = await db.payment_attempts.find_one({"provider_payload.id": order_id})
        if not attempt:
            return {"status": "ignored", "reason": "order not found"}
        
        donation_id = attempt['donation_id']
        
        # Check if already processed (idempotency)
        donation = await db.donations.find_one({"id": donation_id})
        if donation['status'] == 'success':
            return {"status": "already_processed"}
        
        # Update donation
        await db.donations.update_one(
            {"id": donation_id},
            {
                "$set": {
                    "status": "success",
                    "payment_ref": payment_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Generate receipt
        await generate_receipt_background(donation_id)
        
    return {"status": "ok"}

# Include the router in the main app
app.include_router(api_router)

# Mount static files for receipts
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== GENERAL DONATION (NO CAMPAIGN) ====================

@api_router.post("/donations/general")
async def create_general_donation(
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Create general donation to foundation (no campaign required)"""
    
    donation = Donation(
        campaign_id=None,  # No campaign
        amount=amount,
        currency="INR",
        user_id=current_user['sub'],
        type="GENERAL"
    )
    
    donation_dict = donation.model_dump()
    donation_dict['created_at'] = donation_dict['created_at'].isoformat()
    donation_dict['updated_at'] = donation_dict['updated_at'].isoformat()
    
    await db.donations.insert_one(donation_dict)
    
    user_doc = await db.users.find_one({"id": current_user['sub']})
    order = await payment_service.create_order(
        amount=amount,
        currency="INR",
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

# ==================== BLOOD DONOR ENDPOINTS ====================

@api_router.post("/blood-donors")
async def create_blood_donor(
    donor_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create blood donor with consent"""
    
    donor_id = str(uuid.uuid4())
    donor_dict = {
        "id": donor_id,
        "user_id": current_user['sub'],
        "blood_group": donor_data['blood_group'],
        "phone": donor_data['phone'],
        "email": donor_data.get('email'),
        "full_name": donor_data['full_name'],
        "age": donor_data['age'],
        "weight": donor_data['weight'],
        "city": donor_data.get('city'),
        "state": donor_data.get('state'),
        "district": donor_data.get('district'),
        "availability": True,
        "last_donation_date": donor_data.get('last_donation_date'),
        "consent_public": donor_data.get('consent_public', False),
        "consent_public_at": datetime.now(timezone.utc).isoformat() if donor_data.get('consent_public') else None,
        "moderation_hidden": False,
        "contact_reveal_count": 0,
        "created_by": current_user['sub'],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.blood_donors.insert_one(donor_dict)
    
    return {"status": "success", "id": donor_id, "message": "Blood donor registered successfully"}

@api_router.get("/blood-donors/search")
async def search_blood_donors(
    group: str,
    state: Optional[str] = None,
    district: Optional[str] = None
):
    """Public search for blood donors"""
    query = {
        "blood_group": group,
        "consent_public": True,
        "moderation_hidden": False
    }
    
    if state:
        query['state'] = state
    if district:
        query['district'] = district
    
    donors = await db.blood_donors.find(query, {"_id": 0, "created_by": 0}).to_list(100)
    
    for donor in donors:
        if donor.get('phone'):
            donor['phone_masked'] = donor['phone'][:3] + "***" + donor['phone'][-2:]
            del donor['phone']
    
    return donors

# ==================== ADMIN SITE SETTINGS ====================

@api_router.get("/admin/settings")
async def get_site_settings(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get site settings"""
    settings = await db.site_settings.find_one({}, {"_id": 0})
    if not settings:
        # Default settings
        settings = {
            "foundation_name": "WeForYou Foundation",
            "phone": "+91-11-12345678",
            "email": "donations@weforyou.org",
            "address": "123 Charity Street, New Delhi, 110001",
            "about_us": "We are a registered non-profit organization...",
            "pan": "AAATW1234E",
            "registration_number": "U85100DL2020NPL123456"
        }
    return settings

@api_router.patch("/admin/settings")
async def update_site_settings(
    settings_data: dict,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update site settings"""
    await db.site_settings.update_one(
        {},
        {"$set": settings_data},
        upsert=True
    )
    return {"status": "success", "message": "Settings updated"}

# ==================== ADMIN DATA EXPORTS ====================

@api_router.get("/admin/export/users")
async def export_users(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Export all users data"""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(10000)
    return users

@api_router.get("/admin/export/volunteers")
async def export_volunteers(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Export volunteers data with stats"""
    volunteers = await db.users.find({"roles": "volunteer"}, {"_id": 0, "password_hash": 0}).to_list(10000)
    return volunteers

@api_router.get("/admin/export/transactions")
async def export_transactions(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Export all transactions"""
    transactions = await db.donations.find({}, {"_id": 0}).to_list(10000)
    return transactions

@api_router.get("/admin/export/campaigns")
async def export_campaigns(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Export campaigns data"""
    campaigns = await db.campaigns.find({}, {"_id": 0}).to_list(10000)
    return campaigns

@api_router.get("/admin/export/blood-donors")
async def export_blood_donors(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Export blood donors data"""
    donors = await db.blood_donors.find({}, {"_id": 0}).to_list(10000)
    return donors

# ==================== ADMIN EVENTS MANAGEMENT ====================

@api_router.post("/admin/events")
async def create_event(
    event_data: dict,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin creates event"""
    event_id = str(uuid.uuid4())
    event_dict = {
        "id": event_id,
        "title": event_data['title'],
        "description": event_data['description'],
        "schedule_start": event_data['schedule_start'],
        "schedule_end": event_data.get('schedule_end'),
        "venue": event_data.get('venue'),
        "capacity": event_data.get('capacity'),
        "fee_enabled": event_data.get('fee_enabled', False),
        "fee_amount": event_data.get('fee_amount'),
        "image_url": event_data.get('image_url'),
        "created_by": current_user['sub'],
        "status": "LIVE",
        "registered_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.events.insert_one(event_dict)
    return {"status": "success", "id": event_id}

@api_router.patch("/admin/events/{event_id}")
async def update_event(
    event_id: str,
    event_data: dict,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update event"""
    event_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.events.update_one({"id": event_id}, {"$set": event_data})
    return {"status": "success"}

@api_router.delete("/admin/events/{event_id}")
async def delete_event(
    event_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Delete event"""
    await db.events.delete_one({"id": event_id})
    return {"status": "success", "message": "Event deleted"}

@api_router.get("/admin/events")
async def get_all_events_admin(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all events for admin"""
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    return events

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()