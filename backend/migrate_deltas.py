"""
Idempotent migration script for delta features
Run: python migrate_deltas.py
"""
import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def run_migrations():
    print("Starting idempotent migrations...")
    
    # Create collections if not exist
    collections = await db.list_collection_names()
    
    if 'blood_donors' not in collections:
        await db.create_collection('blood_donors')
        print("✓ Created blood_donors collection")
    
    if 'events' not in collections:
        await db.create_collection('events')
        print("✓ Created events collection")
    
    if 'volunteer_activities' not in collections:
        await db.create_collection('volunteer_activities')
        print("✓ Created volunteer_activities collection")
    
    if 'certificates' not in collections:
        await db.create_collection('certificates')
        print("✓ Created certificates collection")
    
    if 'sponsors' not in collections:
        await db.create_collection('sponsors')
        print("✓ Created sponsors collection")
    
    if 'banners' not in collections:
        await db.create_collection('banners')
        print("✓ Created banners collection")
    
    if 'members' not in collections:
        await db.create_collection('members')
        print("✓ Created members collection")
    
    # Migrate existing donations to add type field (default to CAMPAIGN)
    result = await db.donations.update_many(
        {"type": {"$exists": False}},
        {"$set": {"type": "CAMPAIGN"}}
    )
    print(f"✓ Added type field to {result.modified_count} existing donations")
    
    # Migrate existing campaigns to add new fields
    result = await db.campaigns.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "active"}}
    )
    print(f"✓ Added status field to {result.modified_count} existing campaigns")
    
    # Backfill consent fields for members
    result = await db.members.update_many(
        {"consent_public_donor": {"$exists": False}},
        {"$set": {
            "consent_public_donor": False,
            "consent_marketing": False
        }}
    )
    print(f"✓ Added consent fields to {result.modified_count} members")
    
    # Create indexes for performance
    await db.blood_donors.create_index([("blood_group", 1), ("consent_public", 1)])
    await db.blood_donors.create_index([("state", 1), ("district", 1)])
    await db.donations.create_index([("type", 1), ("status", 1)])
    await db.events.create_index([("status", 1), ("schedule_start", 1)])
    print("✓ Created indexes")
    
    print("\n✅ All migrations completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migrations())
    client.close()
