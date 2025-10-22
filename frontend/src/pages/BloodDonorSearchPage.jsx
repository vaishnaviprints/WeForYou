import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import Navbar from '@/components/Navbar';
import { API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Search, Phone, Mail, MapPin, Droplet, AlertCircle, Shield } from 'lucide-react';

const BloodDonorSearchPage = () => {
  const navigate = useNavigate();
  const [donors, setDonors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState({
    group: '',
    state: '',
    district: ''
  });
  const [selectedDonor, setSelectedDonor] = useState(null);
  const [showContactDialog, setShowContactDialog] = useState(false);
  const [captchaToken, setCaptchaToken] = useState('mock_captcha_token');
  const [revealedContact, setRevealedContact] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchParams.group) {
      toast.error('Blood group is required');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('group', searchParams.group);
      if (searchParams.state) params.append('state', searchParams.state);
      if (searchParams.district) params.append('district', searchParams.district);

      const response = await axios.get(`${API}/blood-donors/search?${params.toString()}`);
      setDonors(response.data);
      
      if (response.data.length === 0) {
        toast.info('No donors found matching your criteria');
      }
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRevealContact = async (donor) => {
    setSelectedDonor(donor);
    setShowContactDialog(true);
  };

  const confirmReveal = async () => {
    try {
      const response = await axios.post(
        `${API}/blood-donors/${selectedDonor.id}/reveal-contact?captcha_token=${captchaToken}`
      );
      
      setRevealedContact(response.data);
      toast.success('Contact revealed successfully');
    } catch (error) {
      if (error.response?.status === 429) {
        toast.error('Daily reveal limit reached (5 per day)');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to reveal contact');
      }
      setShowContactDialog(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-pink-50">
      <Navbar />

      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <Droplet className="w-10 h-10 text-red-600" />
            <h1 className="text-4xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
              Blood Donor Directory
            </h1>
          </div>
          <p className="text-gray-600">Find willing blood donors in your area</p>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        {/* Search Form */}
        <Card className="border-0 shadow-lg mb-8">
          <CardHeader>
            <CardTitle>Search for Donors</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-4" data-testid="donor-search-form">
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="group">Blood Group *</Label>
                  <Select
                    value={searchParams.group}
                    onValueChange={(value) => setSearchParams({...searchParams, group: value})}
                  >
                    <SelectTrigger data-testid="search-blood-group">
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

                <div>
                  <Label htmlFor="state">State (Optional)</Label>
                  <Input
                    id="state"
                    placeholder="e.g., Telangana"
                    value={searchParams.state}
                    onChange={(e) => setSearchParams({...searchParams, state: e.target.value})}
                    data-testid="search-state"
                  />
                </div>

                <div>
                  <Label htmlFor="district">District (Optional)</Label>
                  <Input
                    id="district"
                    placeholder="e.g., Hyderabad"
                    value={searchParams.district}
                    onChange={(e) => setSearchParams({...searchParams, district: e.target.value})}
                    data-testid="search-district"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-red-600 hover:bg-red-700"
                data-testid="search-donors-btn"
              >
                <Search className="w-4 h-4 mr-2" />
                {loading ? 'Searching...' : 'Search Donors'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Privacy Notice */}
        <Card className="border-0 shadow-lg mb-8 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-gray-700">
                <p className="font-semibold mb-1">Privacy & Safety</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>All donors have consented to share their contact publicly</li>
                  <li>Contact reveal is rate-limited (5 per day per user)</li>
                  <li>Please use contact information responsibly</li>
                  <li>Report any misuse to admin</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {donors.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Found {donors.length} Donor(s)</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {donors.map((donor) => (
                <Card key={donor.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow" data-testid={`donor-card-${donor.id}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-xl">{donor.full_name}</CardTitle>
                        <Badge className="mt-2 bg-red-600 text-white text-lg">
                          <Droplet className="w-4 h-4 mr-1" />
                          {donor.blood_group}
                        </Badge>
                      </div>
                      {donor.availability && (
                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                          Available
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <MapPin className="w-4 h-4" />
                        <span>{donor.city || 'N/A'}, {donor.state || 'N/A'}</span>
                      </div>

                      <div className="flex items-center gap-2 text-gray-600">
                        <Phone className="w-4 h-4" />
                        <span>{donor.phone_masked || '***-***-****'}</span>
                      </div>

                      {donor.last_donation_date && (
                        <div className="text-xs text-gray-500">
                          Last donation: {new Date(donor.last_donation_date).toLocaleDateString()}
                        </div>
                      )}

                      <Button
                        onClick={() => handleRevealContact(donor)}
                        className="w-full mt-4 bg-red-600 hover:bg-red-700"
                        data-testid={`reveal-contact-${donor.id}`}
                      >
                        Reveal Contact
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* CTA for Registration */}
        <Card className="border-0 shadow-lg mt-12 bg-gradient-to-r from-red-600 to-pink-600 text-white">
          <CardContent className="py-12 text-center">
            <h3 className="text-3xl font-bold mb-4">Want to Save Lives?</h3>
            <p className="text-lg mb-6 opacity-90">Register as a blood donor and help people in need</p>
            <Button
              onClick={() => navigate('/blood-donors/register')}
              size="lg"
              className="bg-white text-red-600 hover:bg-gray-100"
              data-testid="register-donor-cta"
            >
              Register as Donor
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Contact Reveal Dialog */}
      <Dialog open={showContactDialog} onOpenChange={setShowContactDialog}>
        <DialogContent data-testid="reveal-contact-dialog">
          <DialogHeader>
            <DialogTitle>Reveal Donor Contact</DialogTitle>
            <DialogDescription>
              {revealedContact ? (
                <div className="space-y-3 pt-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="font-semibold text-green-800 mb-2">Contact Information:</p>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4" />
                        <span className="font-mono">{revealedContact.phone}</span>
                      </div>
                      {revealedContact.email && (
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4" />
                          <span className="font-mono">{revealedContact.email}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-gray-600 p-3 bg-yellow-50 rounded">
                    <AlertCircle className="w-4 h-4 inline mr-1" />
                    Please be respectful and use this information only for blood donation requests.
                  </div>
                </div>
              ) : (
                <div className="space-y-4 pt-4">
                  <p>You are about to reveal the contact information of <strong>{selectedDonor?.full_name}</strong>.</p>
                  <div className="p-3 bg-yellow-50 rounded text-sm">
                    <AlertCircle className="w-4 h-4 inline mr-1" />
                    <strong>Note:</strong> You have a limit of 5 reveals per day. Use responsibly.
                  </div>
                </div>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            {revealedContact ? (
              <Button onClick={() => setShowContactDialog(false)} data-testid="close-reveal-dialog">
                Close
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={() => setShowContactDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={confirmReveal} className="bg-red-600 hover:bg-red-700" data-testid="confirm-reveal">
                  Confirm & Reveal
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BloodDonorSearchPage;