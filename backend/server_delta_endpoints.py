"""
Delta API endpoints - Add these to existing server.py
These are ONLY the new endpoints for delta features
"""

# Add these imports to server.py
from models_delta import (
    Member, MemberCreate,
    BloodDonor, BloodDonorCreate,
    Event, EventCreate, EventRegistration,
    VolunteerActivity, VolunteerActivityCreate,
    Certificate, Sponsor, SponsorCreate,
    Banner, BannerCreate, DonationType
)

# ==================== MEMBER MANAGEMENT (Volunteers Only) ====================

@api_router.post("/volunteer/members/create", response_model=Member)
async def volunteer_create_member(
    member_data: MemberCreate,
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Volunteer creates a member (no delete allowed)"""
    member = Member(
        **member_data.model_dump(),
        created_by=current_user['sub']
    )
    
    member_dict = member.model_dump()
    member_dict['created_at'] = member_dict['created_at'].isoformat()
    member_dict['updated_at'] = member_dict['updated_at'].isoformat()
    
    await db.members.insert_one(member_dict)
    
    return member

@api_router.get("/volunteer/members")
async def volunteer_get_members(
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Get volunteer's created members"""
    members = await db.members.find(
        {"created_by": current_user['sub']},
        {"_id": 0}
    ).to_list(1000)
    
    for member in members:
        if isinstance(member.get('created_at'), str):
            member['created_at'] = datetime.fromisoformat(member['created_at'])
        if isinstance(member.get('updated_at'), str):
            member['updated_at'] = datetime.fromisoformat(member['updated_at'])
    
    return members

@api_router.patch("/volunteer/members/{member_id}")
async def volunteer_update_member(
    member_id: str,
    member_data: dict,
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Update member (volunteer can only update own created members)"""
    member = await db.members.find_one({"id": member_id, "created_by": current_user['sub']})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found or access denied")
    
    member_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": member_data}
    )
    
    return {"status": "success"}

# ==================== BLOOD DONOR DIRECTORY (Consent-based) ====================

@api_router.post("/blood-donors", response_model=BloodDonor)
async def create_blood_donor(
    donor_data: BloodDonorCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create blood donor with mandatory consent"""
    if not donor_data.consent_public:
        raise HTTPException(status_code=400, detail="Public consent is required to list as blood donor")
    
    # Verify member or user exists
    if donor_data.member_id:
        member = await db.members.find_one({"id": donor_data.member_id})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
    
    donor = BloodDonor(
        **donor_data.model_dump(),
        created_by=current_user['sub'],
        consent_public_at=datetime.now(timezone.utc) if donor_data.consent_public else None
    )
    
    donor_dict = donor.model_dump()
    donor_dict['created_at'] = donor_dict['created_at'].isoformat()
    donor_dict['updated_at'] = donor_dict['updated_at'].isoformat()
    if donor_dict.get('consent_public_at'):
        donor_dict['consent_public_at'] = donor_dict['consent_public_at'].isoformat()
    
    await db.blood_donors.insert_one(donor_dict)
    
    # Log consent event
    await db.audit_logs.insert_one({
        "event": "donor_consent_granted",
        "donor_id": donor.id,
        "user_id": current_user['sub'],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return donor

@api_router.patch("/blood-donors/{donor_id}/consent")
async def toggle_donor_consent(
    donor_id: str,
    consent_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Toggle donor public listing consent"""
    donor = await db.blood_donors.find_one({"id": donor_id})
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    # Check permission
    if donor['created_by'] != current_user['sub'] and 'admin' not in current_user.get('roles', []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    consent_public = consent_data.get('consent_public', False)
    
    update_data = {
        "consent_public": consent_public,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if consent_public:
        update_data['consent_public_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.blood_donors.update_one(
        {"id": donor_id},
        {"$set": update_data}
    )
    
    # Log consent event
    event = "donor_consent_granted" if consent_public else "donor_consent_withdrawn"
    await db.audit_logs.insert_one({
        "event": event,
        "donor_id": donor_id,
        "user_id": current_user['sub'],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "success", "consent_public": consent_public}

@api_router.get("/blood-donors/search")
async def search_blood_donors(
    group: str = Query(..., description="Blood group (required)"),
    state: Optional[str] = None,
    district: Optional[str] = None,
    available: bool = True
):
    """Public search for blood donors (consent + not hidden only)"""
    query = {
        "blood_group": group,
        "consent_public": True,
        "moderation_hidden": False
    }
    
    if state:
        query['state'] = state
    if district:
        query['district'] = district
    if available:
        query['availability'] = True
    
    donors = await db.blood_donors.find(
        query,
        {"_id": 0, "created_by": 0}  # Hide creator info
    ).to_list(100)
    
    for donor in donors:
        if isinstance(donor.get('created_at'), str):
            donor['created_at'] = datetime.fromisoformat(donor['created_at'])
        # Mask phone partially for privacy until reveal
        if donor.get('phone'):
            donor['phone_masked'] = donor['phone'][:3] + "***" + donor['phone'][-2:]
            del donor['phone']
    
    return donors

@api_router.post("/blood-donors/{donor_id}/reveal-contact")
async def reveal_donor_contact(
    donor_id: str,
    captcha_token: str = Query(..., description="Captcha verification"),
    current_user: dict = Depends(get_current_user)
):
    """Reveal donor contact with rate limit and captcha"""
    # TODO: Verify captcha token (integrate with your captcha provider)
    
    donor = await db.blood_donors.find_one({"id": donor_id})
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    if not donor.get('consent_public') or donor.get('moderation_hidden'):
        raise HTTPException(status_code=403, detail="Donor contact not available")
    
    # Rate limit check (max 5 reveals per user per day)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    reveal_count = await db.contact_reveals.count_documents({
        "user_id": current_user['sub'],
        "revealed_at": {"$gte": today_start.isoformat()}
    })
    
    if reveal_count >= 5:
        raise HTTPException(status_code=429, detail="Daily reveal limit reached")
    
    # Log reveal
    await db.contact_reveals.insert_one({
        "donor_id": donor_id,
        "user_id": current_user['sub'],
        "revealed_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Increment reveal count
    await db.blood_donors.update_one(
        {"id": donor_id},
        {"$inc": {"contact_reveal_count": 1}}
    )
    
    return {
        "phone": donor.get('phone'),
        "email": donor.get('email')
    }

@api_router.post("/admin/blood-donors/{donor_id}/hide")
async def admin_hide_donor(
    donor_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin soft-hides donor for moderation"""
    await db.blood_donors.update_one(
        {"id": donor_id},
        {"$set": {"moderation_hidden": True}}
    )
    
    await db.audit_logs.insert_one({
        "event": "donor_moderation_hide",
        "donor_id": donor_id,
        "admin_id": current_user['sub'],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "success"}

# ==================== EVENTS WITH FEE TOGGLE ====================

@api_router.post("/admin/events", response_model=Event)
async def create_event(
    event_data: EventCreate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Admin creates event"""
    if event_data.fee_enabled and not event_data.fee_amount:
        raise HTTPException(status_code=400, detail="Fee amount required when fee is enabled")
    
    event = Event(
        **event_data.model_dump(),
        created_by=current_user['sub']
    )
    
    event_dict = event.model_dump()
    event_dict['schedule_start'] = event_dict['schedule_start'].isoformat()
    if event_dict.get('schedule_end'):
        event_dict['schedule_end'] = event_dict['schedule_end'].isoformat()
    event_dict['created_at'] = event_dict['created_at'].isoformat()
    event_dict['updated_at'] = event_dict['updated_at'].isoformat()
    
    await db.events.insert_one(event_dict)
    
    return event

@api_router.get("/events")
async def get_events(status: Optional[str] = "LIVE"):
    """Get public events"""
    query = {}
    if status:
        query['status'] = status
    
    events = await db.events.find(query, {"_id": 0}).to_list(100)
    
    for event in events:
        if isinstance(event.get('schedule_start'), str):
            event['schedule_start'] = datetime.fromisoformat(event['schedule_start'])
        if event.get('schedule_end') and isinstance(event['schedule_end'], str):
            event['schedule_end'] = datetime.fromisoformat(event['schedule_end'])
    
    return events

@api_router.post("/events/{event_id}/register")
async def register_for_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Register for event (with payment if fee enabled)"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event['status'] != 'LIVE':
        raise HTTPException(status_code=400, detail="Event is not open for registration")
    
    # Check capacity
    if event.get('capacity') and event['registered_count'] >= event['capacity']:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Check if already registered
    existing = await db.event_registrations.find_one({"event_id": event_id, "user_id": current_user['sub']})
    if existing:
        raise HTTPException(status_code=400, detail="Already registered")
    
    if event.get('fee_enabled'):
        # Create donation of type EVENT_FEE
        donation = Donation(
            campaign_id=None,
            amount=event['fee_amount'],
            currency="INR",
            user_id=current_user['sub'],
            type="EVENT_FEE"
        )
        
        donation_dict = donation.model_dump()
        donation_dict['created_at'] = donation_dict['created_at'].isoformat()
        donation_dict['updated_at'] = donation_dict['updated_at'].isoformat()
        
        await db.donations.insert_one(donation_dict)
        
        # Create payment order
        user_doc = await db.users.find_one({"id": current_user['sub']})
        order = await payment_service.create_order(
            amount=event['fee_amount'],
            currency="INR",
            donation_id=donation.id,
            user_email=user_doc['email']
        )
        
        # Create registration with pending payment
        registration = EventRegistration(
            event_id=event_id,
            user_id=current_user['sub'],
            payment_required=True,
            payment_status="PENDING",
            donation_id=donation.id
        )
        
        reg_dict = registration.model_dump()
        reg_dict['registered_at'] = reg_dict['registered_at'].isoformat()
        await db.event_registrations.insert_one(reg_dict)
        
        return {
            "status": "payment_required",
            "donation_id": donation.id,
            "order": order,
            "razorpay_key": payment_service.razorpay_key_id or "mock_key"
        }
    else:
        # Free registration
        registration = EventRegistration(
            event_id=event_id,
            user_id=current_user['sub'],
            payment_required=False
        )
        
        reg_dict = registration.model_dump()
        reg_dict['registered_at'] = reg_dict['registered_at'].isoformat()
        await db.event_registrations.insert_one(reg_dict)
        
        # Increment registered count
        await db.events.update_one(
            {"id": event_id},
            {"$inc": {"registered_count": 1}}
        )
        
        return {"status": "success", "message": "Registered successfully"}

# ==================== ON-BEHALF DONATIONS ====================

@api_router.post("/volunteer/donate-on-behalf")
async def volunteer_donate_on_behalf(
    donation_data: dict,
    current_user: dict = Depends(require_role(["volunteer"]))
):
    """Volunteer donates on behalf of a donor (volunteer pays, donor gets receipt)"""
    campaign = await db.campaigns.find_one({"id": donation_data['campaign_id']})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get member info for receipt
    member = await db.members.find_one({"id": donation_data['donor_member_id']})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Create donation with ON_BEHALF type
    donation = Donation(
        campaign_id=donation_data['campaign_id'],
        amount=donation_data['amount'],
        currency="INR",
        type="ON_BEHALF",
        user_id=current_user['sub'],  # Volunteer pays
        donor_member_id=donation_data['donor_member_id'],  # Actual donor for receipt
        donor_name=member['full_name'],
        donor_phone=member.get('phone'),
        collected_by=current_user.get('volunteer_id'),
        want_80g=donation_data.get('want_80g', False),
        pan=member.get('pan') if donation_data.get('want_80g') else None
    )
    
    donation_dict = donation.model_dump()
    donation_dict['created_at'] = donation_dict['created_at'].isoformat()
    donation_dict['updated_at'] = donation_dict['updated_at'].isoformat()
    
    await db.donations.insert_one(donation_dict)
    
    # Create payment order (volunteer pays)
    volunteer = await db.users.find_one({"id": current_user['sub']})
    order = await payment_service.create_order(
        amount=donation_data['amount'],
        currency="INR",
        donation_id=donation.id,
        user_email=volunteer['email']
    )
    
    return {
        "donation_id": donation.id,
        "order": order,
        "razorpay_key": payment_service.razorpay_key_id or "mock_key",
        "note": f"You are paying on behalf of {member['full_name']}. Receipt will be in their name."
    }

# Additional endpoints continue...
