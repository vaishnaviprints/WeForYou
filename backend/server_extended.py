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

