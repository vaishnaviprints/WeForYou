import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def seed_data():
    print("Starting data seeding...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.campaigns.delete_many({})
    await db.donations.delete_many({})
    await db.receipts.delete_many({})
    await db.pledges.delete_many({})
    print("Cleared existing data")
    
    # Create admin user
    from auth import hash_password
    
    admin_user = {
        "id": "admin-001",
        "email": "admin@weforyou.org",
        "full_name": "Admin User",
        "phone": "+91-9876543210",
        "roles": ["admin", "donor"],
        "password_hash": hash_password("admin123"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    await db.users.insert_one(admin_user)
    print(f"Created admin user: {admin_user['email']} / admin123")
    
    # Create 3 donor users
    donors = [
        {
            "id": "donor-001",
            "email": "priya.sharma@example.com",
            "full_name": "Priya Sharma",
            "phone": "+91-9876543211",
            "roles": ["donor"],
            "password_hash": hash_password("donor123"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        },
        {
            "id": "donor-002",
            "email": "rahul.verma@example.com",
            "full_name": "Rahul Verma",
            "phone": "+91-9876543212",
            "roles": ["donor"],
            "password_hash": hash_password("donor123"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        },
        {
            "id": "donor-003",
            "email": "anita.patel@example.com",
            "full_name": "Anita Patel",
            "phone": "+91-9876543213",
            "roles": ["donor"],
            "password_hash": hash_password("donor123"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
    ]
    await db.users.insert_many(donors)
    print(f"Created {len(donors)} donor users (password: donor123)")
    
    # Create 1 campaign
    campaign = {
        "id": "campaign-001",
        "title": "Education for Underprivileged Children",
        "description": "Help us provide quality education to children from underprivileged backgrounds. Your donation will cover school fees, books, uniforms, and learning materials for children who otherwise wouldn't have access to education.\n\nEvery child deserves the opportunity to learn and grow. With your support, we can make a difference in their lives and help them build a better future.",
        "goal_amount": 500000.0,
        "currency": "INR",
        "allow_recurring": True,
        "image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800",
        "created_by": "admin-001",
        "current_amount": 85000.0,
        "donor_count": 3,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    }
    await db.campaigns.insert_one(campaign)
    print(f"Created campaign: {campaign['title']}")
    
    # Create 5 donations with varied statuses
    donations = [
        {
            "id": "donation-001",
            "user_id": "donor-001",
            "campaign_id": "campaign-001",
            "amount": 50000.0,
            "currency": "INR",
            "status": "success",
            "payment_provider": "razorpay",
            "payment_ref": "pay_mock_1234567890",
            "method": "upi",
            "is_anonymous": False,
            "want_80g": True,
            "pan": "ABCDE1234F",
            "legal_name": "Priya Sharma",
            "address": "123 MG Road, Bangalore - 560001",
            "receipt_id": "receipt-001",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        },
        {
            "id": "donation-002",
            "user_id": "donor-002",
            "campaign_id": "campaign-001",
            "amount": 25000.0,
            "currency": "INR",
            "status": "success",
            "payment_provider": "razorpay",
            "payment_ref": "pay_mock_1234567891",
            "method": "card",
            "is_anonymous": True,
            "want_80g": False,
            "pan": None,
            "legal_name": None,
            "address": None,
            "receipt_id": "receipt-002",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        },
        {
            "id": "donation-003",
            "user_id": "donor-003",
            "campaign_id": "campaign-001",
            "amount": 10000.0,
            "currency": "INR",
            "status": "success",
            "payment_provider": "razorpay",
            "payment_ref": "pay_mock_1234567892",
            "method": "netbanking",
            "is_anonymous": False,
            "want_80g": True,
            "pan": "XYZAB9876C",
            "legal_name": "Anita Patel",
            "address": "456 Park Street, Mumbai - 400001",
            "receipt_id": "receipt-003",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        },
        {
            "id": "donation-004",
            "user_id": "donor-001",
            "campaign_id": "campaign-001",
            "amount": 5000.0,
            "currency": "INR",
            "status": "pending",
            "payment_provider": "razorpay",
            "payment_ref": None,
            "method": None,
            "is_anonymous": False,
            "want_80g": False,
            "pan": None,
            "legal_name": None,
            "address": None,
            "receipt_id": None,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        },
        {
            "id": "donation-005",
            "user_id": "donor-002",
            "campaign_id": "campaign-001",
            "amount": 3000.0,
            "currency": "INR",
            "status": "failed",
            "payment_provider": "razorpay",
            "payment_ref": None,
            "method": None,
            "is_anonymous": False,
            "want_80g": False,
            "pan": None,
            "legal_name": None,
            "address": None,
            "receipt_id": None,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        }
    ]
    await db.donations.insert_many(donations)
    print(f"Created {len(donations)} donations (3 success, 1 pending, 1 failed)")
    
    # Create receipts for successful donations
    receipts = [
        {
            "id": "receipt-001",
            "donation_id": "donation-001",
            "receipt_number": "WFY202400001",
            "pdf_url": "receipts/2024-25/WFY-WFY202400001-2024-25.pdf",
            "issued_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "fy": "2024-25",
            "section_80g": True,
            "ack_no": "80G/2024/001"
        },
        {
            "id": "receipt-002",
            "donation_id": "donation-002",
            "receipt_number": "WFY202400002",
            "pdf_url": "receipts/2024-25/WFY-WFY202400002-2024-25.pdf",
            "issued_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            "fy": "2024-25",
            "section_80g": False,
            "ack_no": None
        },
        {
            "id": "receipt-003",
            "donation_id": "donation-003",
            "receipt_number": "WFY202400003",
            "pdf_url": "receipts/2024-25/WFY-WFY202400003-2024-25.pdf",
            "issued_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "fy": "2024-25",
            "section_80g": True,
            "ack_no": "80G/2024/002"
        }
    ]
    await db.receipts.insert_many(receipts)
    print(f"Created {len(receipts)} receipts")
    
    print("\n=== SEED DATA SUMMARY ===")
    print(f"Admin: admin@weforyou.org / admin123")
    print(f"Donors:")
    print(f"  - priya.sharma@example.com / donor123")
    print(f"  - rahul.verma@example.com / donor123")
    print(f"  - anita.patel@example.com / donor123")
    print(f"Campaign: {campaign['title']}")
    print(f"Donations: 3 successful, 1 pending, 1 failed")
    print(f"Total raised: ₹{campaign['current_amount']:,.2f}")
    print("\nSeeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
    client.close()