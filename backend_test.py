#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class WeForYouAPITester:
    def __init__(self, base_url="https://donation-login-only.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.donor_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.admin_credentials = {
            "email": "admin@weforyou.org",
            "password": "admin123"
        }
        self.donor_credentials = {
            "email": "priya.sharma@example.com", 
            "password": "donor123"
        }
        self.new_donor_data = {
            "email": f"test_donor_{int(time.time())}@example.com",
            "password": "testpass123",
            "full_name": "Test Donor",
            "phone": "9876543210",
            "roles": ["donor"]
        }

    def log_test(self, name, success, details="", endpoint=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "endpoint": endpoint
        })

    def make_request(self, method, endpoint, data=None, token=None, expect_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expect_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data
            
        except Exception as e:
            return False, {"error": str(e)}

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.make_request(
            'POST', 'auth/login', 
            self.admin_credentials, 
            expect_status=200
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log_test("Admin Login", True, endpoint="auth/login")
            return True
        else:
            self.log_test("Admin Login", False, str(response), "auth/login")
            return False

    def test_donor_login(self):
        """Test donor login"""
        success, response = self.make_request(
            'POST', 'auth/login', 
            self.donor_credentials, 
            expect_status=200
        )
        
        if success and 'access_token' in response:
            self.donor_token = response['access_token']
            self.log_test("Donor Login", True, endpoint="auth/login")
            return True
        else:
            self.log_test("Donor Login", False, str(response), "auth/login")
            return False

    def test_donor_registration(self):
        """Test new donor registration"""
        success, response = self.make_request(
            'POST', 'auth/register', 
            self.new_donor_data, 
            expect_status=200
        )
        
        if success and 'access_token' in response:
            self.log_test("Donor Registration", True, endpoint="auth/register")
            return True
        else:
            self.log_test("Donor Registration", False, str(response), "auth/register")
            return False

    def test_get_campaigns(self):
        """Test getting campaigns list"""
        success, response = self.make_request('GET', 'campaigns')
        
        if success and isinstance(response, list):
            campaign_count = len(response)
            self.log_test(f"Get Campaigns ({campaign_count} found)", True, endpoint="campaigns")
            return response
        else:
            self.log_test("Get Campaigns", False, str(response), "campaigns")
            return []

    def test_get_campaign_detail(self, campaign_id):
        """Test getting campaign details"""
        success, response = self.make_request('GET', f'campaigns/{campaign_id}')
        
        if success and 'id' in response:
            self.log_test(f"Get Campaign Detail ({response.get('title', 'Unknown')})", True, endpoint=f"campaigns/{campaign_id}")
            return response
        else:
            self.log_test("Get Campaign Detail", False, str(response), f"campaigns/{campaign_id}")
            return None

    def test_create_donation(self, campaign_id):
        """Test creating a donation"""
        if not self.donor_token:
            self.log_test("Create Donation", False, "No donor token available", "donations")
            return None
            
        donation_data = {
            "campaign_id": campaign_id,
            "amount": 1000.0,
            "currency": "INR",
            "is_anonymous": False,
            "want_80g": True,
            "pan": "ABCDE1234F",
            "legal_name": "Test Donor",
            "address": "Test Address"
        }
        
        success, response = self.make_request(
            'POST', 'donations', 
            donation_data, 
            token=self.donor_token,
            expect_status=200
        )
        
        if success and 'donation_id' in response:
            self.log_test("Create Donation", True, endpoint="donations")
            return response
        else:
            self.log_test("Create Donation", False, str(response), "donations")
            return None

    def test_verify_donation(self, donation_id):
        """Test verifying donation (mock payment)"""
        if not self.donor_token:
            self.log_test("Verify Donation", False, "No donor token available", f"donations/{donation_id}/verify")
            return False
            
        payment_data = {
            "razorpay_order_id": f"order_mock_{int(time.time())}",
            "razorpay_payment_id": f"pay_mock_{int(time.time())}",
            "razorpay_signature": "mock_signature"
        }
        
        success, response = self.make_request(
            'POST', f'donations/{donation_id}/verify', 
            payment_data, 
            token=self.donor_token,
            expect_status=200
        )
        
        if success:
            self.log_test("Verify Donation (Mock Payment)", True, endpoint=f"donations/{donation_id}/verify")
            return True
        else:
            self.log_test("Verify Donation (Mock Payment)", False, str(response), f"donations/{donation_id}/verify")
            return False

    def test_get_my_donations(self):
        """Test getting user's donations"""
        if not self.donor_token:
            self.log_test("Get My Donations", False, "No donor token available", "donations/my")
            return []
            
        success, response = self.make_request(
            'GET', 'donations/my', 
            token=self.donor_token
        )
        
        if success and isinstance(response, list):
            donation_count = len(response)
            self.log_test(f"Get My Donations ({donation_count} found)", True, endpoint="donations/my")
            return response
        else:
            self.log_test("Get My Donations", False, str(response), "donations/my")
            return []

    def test_create_pledge(self, campaign_id):
        """Test creating a recurring pledge"""
        if not self.donor_token:
            self.log_test("Create Pledge", False, "No donor token available", "pledges")
            return None
            
        pledge_data = {
            "campaign_id": campaign_id,
            "amount": 500.0,
            "frequency": "monthly"
        }
        
        success, response = self.make_request(
            'POST', 'pledges', 
            pledge_data, 
            token=self.donor_token,
            expect_status=200
        )
        
        if success and 'id' in response:
            self.log_test("Create Pledge", True, endpoint="pledges")
            return response
        else:
            self.log_test("Create Pledge", False, str(response), "pledges")
            return None

    def test_get_my_pledges(self):
        """Test getting user's pledges"""
        if not self.donor_token:
            self.log_test("Get My Pledges", False, "No donor token available", "pledges/my")
            return []
            
        success, response = self.make_request(
            'GET', 'pledges/my', 
            token=self.donor_token
        )
        
        if success and isinstance(response, list):
            pledge_count = len(response)
            self.log_test(f"Get My Pledges ({pledge_count} found)", True, endpoint="pledges/my")
            return response
        else:
            self.log_test("Get My Pledges", False, str(response), "pledges/my")
            return []

    def test_pledge_actions(self, pledge_id):
        """Test pledge pause/cancel/activate actions"""
        if not self.donor_token or not pledge_id:
            self.log_test("Pledge Actions", False, "No donor token or pledge ID", f"pledges/{pledge_id}")
            return False
            
        # Test pause
        success, response = self.make_request(
            'PATCH', f'pledges/{pledge_id}?action=pause', 
            token=self.donor_token
        )
        
        if success:
            self.log_test("Pause Pledge", True, endpoint=f"pledges/{pledge_id}")
        else:
            self.log_test("Pause Pledge", False, str(response), f"pledges/{pledge_id}")
            return False
            
        # Test activate
        success, response = self.make_request(
            'PATCH', f'pledges/{pledge_id}?action=activate', 
            token=self.donor_token
        )
        
        if success:
            self.log_test("Activate Pledge", True, endpoint=f"pledges/{pledge_id}")
            return True
        else:
            self.log_test("Activate Pledge", False, str(response), f"pledges/{pledge_id}")
            return False

    def test_admin_create_campaign(self):
        """Test admin creating a new campaign"""
        if not self.admin_token:
            self.log_test("Admin Create Campaign", False, "No admin token available", "campaigns")
            return None
            
        campaign_data = {
            "title": f"Test Campaign {int(time.time())}",
            "description": "This is a test campaign created by automated testing",
            "goal_amount": 50000.0,
            "currency": "INR",
            "allow_recurring": True
        }
        
        success, response = self.make_request(
            'POST', 'campaigns', 
            campaign_data, 
            token=self.admin_token,
            expect_status=200
        )
        
        if success and 'id' in response:
            self.log_test("Admin Create Campaign", True, endpoint="campaigns")
            return response
        else:
            self.log_test("Admin Create Campaign", False, str(response), "campaigns")
            return None

    def test_admin_get_donors(self):
        """Test admin getting donor directory"""
        if not self.admin_token:
            self.log_test("Admin Get Donors", False, "No admin token available", "admin/donors")
            return []
            
        success, response = self.make_request(
            'GET', 'admin/donors', 
            token=self.admin_token
        )
        
        if success and isinstance(response, list):
            donor_count = len(response)
            self.log_test(f"Admin Get Donors ({donor_count} found)", True, endpoint="admin/donors")
            return response
        else:
            self.log_test("Admin Get Donors", False, str(response), "admin/donors")
            return []

    def test_admin_campaign_analytics(self, campaign_id):
        """Test admin getting campaign analytics"""
        if not self.admin_token:
            self.log_test("Admin Campaign Analytics", False, "No admin token available", f"admin/campaigns/{campaign_id}/analytics")
            return None
            
        success, response = self.make_request(
            'GET', f'admin/campaigns/{campaign_id}/analytics', 
            token=self.admin_token
        )
        
        if success and 'campaign' in response:
            self.log_test("Admin Campaign Analytics", True, endpoint=f"admin/campaigns/{campaign_id}/analytics")
            return response
        else:
            self.log_test("Admin Campaign Analytics", False, str(response), f"admin/campaigns/{campaign_id}/analytics")
            return None

    def test_unauthorized_access(self):
        """Test unauthorized access to admin endpoints"""
        success, response = self.make_request(
            'GET', 'admin/donors', 
            token=self.donor_token,
            expect_status=403
        )
        
        if success:
            self.log_test("Unauthorized Access Prevention", True, endpoint="admin/donors")
            return True
        else:
            self.log_test("Unauthorized Access Prevention", False, "Donor was able to access admin endpoint", "admin/donors")
            return False

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🚀 Starting WeForYou Foundation API Tests")
        print("=" * 50)
        
        # Authentication Tests
        print("\n📝 Authentication Tests")
        admin_login_success = self.test_admin_login()
        donor_login_success = self.test_donor_login()
        self.test_donor_registration()
        
        if not admin_login_success or not donor_login_success:
            print("❌ Critical: Authentication failed. Stopping tests.")
            return self.generate_report()
        
        # Campaign Tests
        print("\n🎯 Campaign Tests")
        campaigns = self.test_get_campaigns()
        
        if campaigns:
            # Test campaign detail
            first_campaign = campaigns[0]
            campaign_detail = self.test_get_campaign_detail(first_campaign['id'])
            
            # Admin Tests
            print("\n👑 Admin Tests")
            new_campaign = self.test_admin_create_campaign()
            self.test_admin_get_donors()
            
            if campaign_detail:
                self.test_admin_campaign_analytics(first_campaign['id'])
            
            # Donation Tests
            print("\n💰 Donation Tests")
            donation_response = self.test_create_donation(first_campaign['id'])
            
            if donation_response:
                donation_id = donation_response['donation_id']
                verify_success = self.test_verify_donation(donation_id)
                
                if verify_success:
                    # Wait a bit for receipt generation
                    time.sleep(2)
                    self.test_get_my_donations()
            
            # Pledge Tests (only if campaign allows recurring)
            if first_campaign.get('allow_recurring', False):
                print("\n🔄 Pledge Tests")
                pledge = self.test_create_pledge(first_campaign['id'])
                pledges = self.test_get_my_pledges()
                
                if pledge:
                    self.test_pledge_actions(pledge['id'])
        
        # Security Tests
        print("\n🔒 Security Tests")
        self.test_unauthorized_access()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_run - self.tests_passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    tester = WeForYouAPITester()
    report = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if report['failed_tests'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())