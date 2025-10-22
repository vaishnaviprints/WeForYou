import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Droplet, Shield, AlertCircle, CheckCircle } from 'lucide-react';

const BloodDonorRegisterPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [loading, setLoading] = useState(false);
  const [showConsentDialog, setShowConsentDialog] = useState(false);
  const [formData, setFormData] = useState(null);
  const [consentAccepted, setConsentAccepted] = useState(false);

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-pink-50">
        <Navbar />
        <div className="container mx-auto px-6 py-20 text-center">
          <Card className="max-w-md mx-auto border-0 shadow-lg">
            <CardContent className="py-12">
              <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-4">Login Required</h2>
              <p className="text-gray-600 mb-6">Please login to register as a blood donor</p>
              <Button onClick={() => navigate('/login')} className="bg-red-600 hover:bg-red-700">
                Go to Login
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = new FormData(e.target);

    const donorData = {
      user_id: user.id,
      blood_group: data.get('blood_group'),
      phone: data.get('phone'),
      email: data.get('email') || null,
      full_name: data.get('full_name'),
      age: parseInt(data.get('age')),
      weight: parseFloat(data.get('weight')),
      city: data.get('city') || null,
      state: data.get('state') || null,
      district: data.get('district') || null,
      last_donation_date: data.get('last_donation_date') || null,
      availability: true
    };

    setFormData(donorData);
    setShowConsentDialog(true);
  };

  const handleConsentAccept = async () => {
    if (!consentAccepted) {
      toast.error('Please accept the consent to proceed');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/blood-donors`, {
        ...formData,
        consent_public: true
      });

      toast.success('Registration successful! You are now publicly listed.');
      navigate('/blood-donors/search');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
      setShowConsentDialog(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-pink-50">
      <Navbar />

      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center gap-3">
            <Droplet className="w-10 h-10 text-red-600" />
            <div>
              <h1 className="text-4xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
                Register as Blood Donor
              </h1>
              <p className="text-gray-600 mt-2">Help save lives by becoming a blood donor</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Info Card */}
          <Card className="border-0 shadow-lg mb-8 bg-blue-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-2">What happens after registration?</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Your contact will be publicly visible in donor search</li>
                    <li>People can search for donors by blood group and location</li>
                    <li>You can withdraw consent anytime from your profile</li>
                    <li>Your information is used only for blood donation requests</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Registration Form */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Donor Information</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6" data-testid="donor-register-form">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="full_name">Full Name *</Label>
                    <Input
                      id="full_name"
                      name="full_name"
                      defaultValue={user.full_name}
                      required
                      data-testid="donor-name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="blood_group">Blood Group *</Label>
                    <Select name="blood_group" required>
                      <SelectTrigger data-testid="donor-blood-group">
                        <SelectValue placeholder="Select blood group" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="A+">A+</SelectItem>
                        <SelectItem value="A-">A-</SelectItem>
                        <SelectItem value="B+">B+</SelectItem>
                        <SelectItem value="B-">B-</SelectItem>
                        <SelectItem value="AB+">AB+</SelectItem>
                        <SelectItem value="AB-">AB-</SelectItem>
                        <SelectItem value="O+">O+</SelectItem>
                        <SelectItem value="O-">O-</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="phone">Phone Number *</Label>
                    <Input
                      id="phone"
                      name="phone"
                      type="tel"
                      defaultValue={user.phone}
                      required
                      data-testid="donor-phone"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      defaultValue={user.email}
                      data-testid="donor-email"
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="age">Age *</Label>
                    <Input
                      id="age"
                      name="age"
                      type="number"
                      min="18"
                      max="65"
                      required
                      data-testid="donor-age"
                    />
                  </div>
                  <div>
                    <Label htmlFor="weight">Weight (kg) *</Label>
                    <Input
                      id="weight"
                      name="weight"
                      type="number"
                      min="45"
                      step="0.1"
                      required
                      data-testid="donor-weight"
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="city">City</Label>
                    <Input id="city" name="city" data-testid="donor-city" />
                  </div>
                  <div>
                    <Label htmlFor="district">District</Label>
                    <Input id="district" name="district" data-testid="donor-district" />
                  </div>
                  <div>
                    <Label htmlFor="state">State</Label>
                    <Input id="state" name="state" data-testid="donor-state" />
                  </div>
                </div>

                <div>
                  <Label htmlFor="last_donation_date">Last Donation Date (if any)</Label>
                  <Input
                    id="last_donation_date"
                    name="last_donation_date"
                    type="date"
                    data-testid="last-donation-date"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Minimum 3 months gap required between donations
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-red-600 hover:bg-red-700 h-12 text-lg"
                  data-testid="submit-donor-registration"
                >
                  Continue to Consent
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Consent Dialog - MANDATORY */}
      <Dialog open={showConsentDialog} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-lg" data-testid="consent-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-2xl">
              <Shield className="w-6 h-6 text-blue-600" />
              Public Listing Consent
            </DialogTitle>
            <DialogDescription>
              <div className="space-y-4 pt-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="font-semibold text-blue-900 mb-2">
                    Your information will be publicly visible:
                  </p>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>✓ Name, Blood Group, Age</li>
                    <li>✓ City, District, State</li>
                    <li>✓ Phone and Email (after rate-limited reveal)</li>
                    <li>✓ Availability status</li>
                  </ul>
                </div>

                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="font-semibold text-green-900 mb-2">
                    You can:
                  </p>
                  <ul className="text-sm text-green-800 space-y-1">
                    <li>✓ Withdraw consent anytime from your profile</li>
                    <li>✓ Update your availability status</li>
                    <li>✓ Report any misuse to admin</li>
                  </ul>
                </div>

                <div className="flex items-start gap-3 p-3 border-2 border-blue-200 rounded-lg">
                  <Checkbox
                    id="consent"
                    checked={consentAccepted}
                    onCheckedChange={setConsentAccepted}
                    data-testid="consent-checkbox"
                  />
                  <label htmlFor="consent" className="text-sm font-medium cursor-pointer">
                    I agree that my contact information may be shown publicly in the blood donor directory. 
                    I understand I can withdraw this consent anytime.
                  </label>
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowConsentDialog(false);
                setConsentAccepted(false);
              }}
              data-testid="cancel-consent"
            >
              Cancel
            </Button>
            <Button
              onClick={handleConsentAccept}
              disabled={!consentAccepted || loading}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="accept-consent"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              {loading ? 'Registering...' : 'Accept & List Publicly'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BloodDonorRegisterPage;
