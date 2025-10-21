import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Heart, Users, Shield } from 'lucide-react';

const CampaignDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDonationModal, setShowDonationModal] = useState(false);
  const [processing, setProcessing] = useState(false);
  
  // Donation form state
  const [amount, setAmount] = useState('');
  const [customAmount, setCustomAmount] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [want80G, setWant80G] = useState(false);
  const [pan, setPan] = useState('');
  const [legalName, setLegalName] = useState('');
  const [address, setAddress] = useState('');

  const presetAmounts = [500, 1000, 2500, 5000];

  useEffect(() => {
    fetchCampaign();
  }, [id]);

  const fetchCampaign = async () => {
    try {
      const response = await axios.get(`${API}/campaigns/${id}`);
      setCampaign(response.data);
    } catch (error) {
      toast.error('Failed to load campaign');
      navigate('/campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleDonate = async () => {
    if (!user) {
      toast.error('Please login to donate');
      navigate('/');
      return;
    }

    const donationAmount = amount === 'custom' ? parseFloat(customAmount) : parseFloat(amount);
    
    if (!donationAmount || donationAmount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (want80G && (!pan || !legalName)) {
      toast.error('PAN and Legal Name are required for 80G receipt');
      return;
    }

    setProcessing(true);

    try {
      const response = await axios.post(`${API}/donations`, {
        campaign_id: id,
        amount: donationAmount,
        currency: 'INR',
        is_anonymous: isAnonymous,
        want_80g: want80G,
        pan: want80G ? pan : null,
        legal_name: want80G ? legalName : null,
        address: want80G ? address : null
      });

      const { donation_id, order, razorpay_key } = response.data;

      // Check if using mock payment
      const isMock = razorpay_key === 'mock_key';

      if (isMock) {
        // Mock payment - auto verify
        await axios.post(`${API}/donations/${donation_id}/verify`, {
          razorpay_order_id: order.id,
          razorpay_payment_id: `pay_mock_${Date.now()}`,
          razorpay_signature: 'mock_signature'
        });
        
        toast.success('Donation successful! Receipt is being generated.');
        setShowDonationModal(false);
        navigate('/my-donations');
      } else {
        // Real Razorpay payment
        const options = {
          key: razorpay_key,
          amount: order.amount,
          currency: order.currency,
          order_id: order.id,
          name: 'WeForYou Foundation',
          description: campaign.title,
          handler: async function (response) {
            try {
              await axios.post(`${API}/donations/${donation_id}/verify`, response);
              toast.success('Donation successful! Receipt is being generated.');
              setShowDonationModal(false);
              navigate('/my-donations');
            } catch (error) {
              toast.error('Payment verification failed');
            }
          },
          prefill: {
            email: user.email,
            name: user.full_name
          },
          theme: {
            color: '#2563eb'
          }
        };

        const rzp = new window.Razorpay(options);
        rzp.open();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Donation failed');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!campaign) return null;

  const progress = Math.min((campaign.current_amount / campaign.goal_amount) * 100, 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-6">
          <Button variant="ghost" onClick={() => navigate('/campaigns')} data-testid="back-campaigns-btn">
            <ArrowLeft className="mr-2" /> Back to Campaigns
          </Button>
        </div>
      </div>

      {/* Campaign Content */}
      <div className="container mx-auto px-6 py-12">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {campaign.image_url && (
              <div className="rounded-2xl overflow-hidden shadow-xl">
                <img 
                  src={campaign.image_url} 
                  alt={campaign.title}
                  className="w-full h-96 object-cover"
                />
              </div>
            )}

            <Card className="border-0 shadow-lg" data-testid="campaign-detail-card">
              <CardHeader>
                <CardTitle className="text-3xl" style={{ fontFamily: 'Space Grotesk' }}>
                  {campaign.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                  {campaign.description}
                </p>
              </CardContent>
            </Card>

            {/* Recent Donors */}
            {campaign.recent_donors && campaign.recent_donors.length > 0 && (
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    Recent Donors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {campaign.recent_donors.map((donor, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium">{donor.name}</span>
                        <span className="text-blue-600 font-semibold">₹{donor.amount.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card className="border-0 shadow-lg sticky top-6" data-testid="donation-widget">
              <CardHeader>
                <CardTitle>Support This Cause</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Progress */}
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-2xl font-bold text-blue-600">
                      ₹{campaign.current_amount.toLocaleString()}
                    </span>
                    <span className="text-gray-500">of ₹{campaign.goal_amount.toLocaleString()}</span>
                  </div>
                  <Progress value={progress} className="h-3" />
                  <p className="text-sm text-gray-500 mt-2">
                    {Math.round(progress)}% funded
                  </p>
                </div>

                <Separator />

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{campaign.donor_count}</p>
                    <p className="text-sm text-gray-600">Donors</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {Math.round((campaign.goal_amount - campaign.current_amount) / 1000)}K
                    </p>
                    <p className="text-sm text-gray-600">To Go</p>
                  </div>
                </div>

                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 text-lg rounded-xl"
                  onClick={() => setShowDonationModal(true)}
                  data-testid="donate-now-btn"
                >
                  <Heart className="mr-2" />
                  Donate Now
                </Button>

                {campaign.allow_recurring && (
                  <p className="text-xs text-center text-gray-500">
                    <Shield className="inline w-3 h-3 mr-1" />
                    Recurring donations available
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Donation Modal */}
      <Dialog open={showDonationModal} onOpenChange={setShowDonationModal}>
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto" data-testid="donation-modal">
          <DialogHeader>
            <DialogTitle className="text-2xl">Make a Donation</DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Amount Selection */}
            <div>
              <Label className="text-base font-semibold mb-3 block">Select Amount</Label>
              <div className="grid grid-cols-2 gap-3 mb-3">
                {presetAmounts.map((preset) => (
                  <Button
                    key={preset}
                    variant={amount === preset.toString() ? 'default' : 'outline'}
                    onClick={() => {
                      setAmount(preset.toString());
                      setCustomAmount('');
                    }}
                    className="h-14 text-lg"
                    data-testid={`amount-preset-${preset}`}
                  >
                    ₹{preset.toLocaleString()}
                  </Button>
                ))}
              </div>
              <Button
                variant={amount === 'custom' ? 'default' : 'outline'}
                onClick={() => setAmount('custom')}
                className="w-full h-14 text-lg"
                data-testid="amount-custom-btn"
              >
                Custom Amount
              </Button>
              {amount === 'custom' && (
                <Input
                  type="number"
                  placeholder="Enter amount"
                  value={customAmount}
                  onChange={(e) => setCustomAmount(e.target.value)}
                  className="mt-3 h-12 text-lg"
                  data-testid="custom-amount-input"
                />
              )}
            </div>

            <Separator />

            {/* Anonymous Toggle */}
            <div className="flex items-center justify-between">
              <Label htmlFor="anonymous" className="flex-1">
                <div className="font-semibold">Donate Anonymously</div>
                <div className="text-sm text-gray-500">Your name won't be displayed publicly</div>
              </Label>
              <Switch
                id="anonymous"
                checked={isAnonymous}
                onCheckedChange={setIsAnonymous}
                data-testid="anonymous-switch"
              />
            </div>

            <Separator />

            {/* 80G Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="want80g" className="flex-1">
                  <div className="font-semibold">I want 80G Tax Receipt</div>
                  <div className="text-sm text-gray-500">Get tax deduction certificate</div>
                </Label>
                <Switch
                  id="want80g"
                  checked={want80G}
                  onCheckedChange={setWant80G}
                  data-testid="80g-switch"
                />
              </div>

              {want80G && (
                <div className="space-y-3 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div>
                    <Label htmlFor="pan">PAN Number *</Label>
                    <Input
                      id="pan"
                      value={pan}
                      onChange={(e) => setPan(e.target.value.toUpperCase())}
                      placeholder="ABCDE1234F"
                      maxLength={10}
                      data-testid="pan-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="legalName">Legal Name (as per PAN) *</Label>
                    <Input
                      id="legalName"
                      value={legalName}
                      onChange={(e) => setLegalName(e.target.value)}
                      placeholder="Full name as per PAN card"
                      data-testid="legal-name-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="address">Address (Optional)</Label>
                    <Input
                      id="address"
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      placeholder="Your address"
                      data-testid="address-input"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Donate Button */}
            <Button
              onClick={handleDonate}
              disabled={processing || !amount}
              className="w-full bg-blue-600 hover:bg-blue-700 h-14 text-lg"
              data-testid="proceed-payment-btn"
            >
              {processing ? 'Processing...' : `Donate ₹${amount === 'custom' ? customAmount : amount}`}
            </Button>

            <p className="text-xs text-center text-gray-500">
              <Shield className="inline w-3 h-3 mr-1" />
              Secure payment powered by Razorpay
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CampaignDetailPage;
