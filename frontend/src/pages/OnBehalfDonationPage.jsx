import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Heart, User, Phone, Mail, AlertCircle } from 'lucide-react';

const OnBehalfDonationPage = () => {
  const { memberId } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [member, setMember] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (!user?.roles?.includes('volunteer')) {
      toast.error('Only volunteers can make on-behalf donations');
      navigate('/');
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [memberRes, campaignsRes] = await Promise.all([
        axios.get(`${API}/volunteer/members`),
        axios.get(`${API}/campaigns?status=active`)
      ]);

      const foundMember = memberRes.data.find(m => m.id === memberId);
      if (!foundMember) {
        toast.error('Member not found');
        navigate('/volunteer/members');
        return;
      }

      setMember(foundMember);
      setCampaigns(campaignsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleDonate = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    setProcessing(true);
    try {
      const response = await axios.post(`${API}/volunteer/donate-on-behalf`, {
        campaign_id: formData.get('campaign_id'),
        donor_member_id: memberId,
        amount: parseFloat(formData.get('amount')),
        want_80g: member.pan ? true : false
      });

      const { donation_id, order, razorpay_key, note } = response.data;

      toast.info(note);

      const isMock = razorpay_key === 'mock_key';

      if (isMock) {
        await axios.post(`${API}/donations/${donation_id}/verify`, {
          razorpay_order_id: order.id,
          razorpay_payment_id: `pay_mock_${Date.now()}`,
          razorpay_signature: 'mock_signature'
        });

        toast.success(`Donation successful on behalf of ${member.full_name}!`);
        navigate('/volunteer/collections');
      } else {
        const options = {
          key: razorpay_key,
          amount: order.amount,
          currency: order.currency,
          order_id: order.id,
          name: 'WeForYou Foundation',
          description: `On behalf of ${member.full_name}`,
          handler: async function (response) {
            try {
              await axios.post(`${API}/donations/${donation_id}/verify`, response);
              toast.success(`Donation successful on behalf of ${member.full_name}!`);
              navigate('/volunteer/collections');
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navbar />

      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
            Donate On Behalf
          </h1>
          <p className="text-gray-600 mt-2">Making donation on behalf of {member?.full_name}</p>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Member Info Card */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Donor Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Name:</span>
                  <p className="font-semibold">{member?.full_name}</p>
                </div>
                <div>
                  <span className="text-gray-500">Phone:</span>
                  <p className="font-semibold">{member?.phone}</p>
                </div>
                {member?.email && (
                  <div>
                    <span className="text-gray-500">Email:</span>
                    <p className="font-semibold">{member?.email}</p>
                  </div>
                )}
                {member?.pan && (
                  <div>
                    <span className="text-gray-500">PAN:</span>
                    <p className="font-semibold">{member?.pan}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Important Notice */}
          <Card className="border-0 shadow-lg bg-yellow-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-1">Important:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>You (volunteer) will pay for this donation</li>
                    <li>Receipt will be issued in <strong>{member?.full_name}'s</strong> name</li>
                    <li>This is an ONLINE payment only (no cash option)</li>
                    {member?.pan && <li>80G tax benefit will be provided to the donor</li>}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Donation Form */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Donation Details</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleDonate} className="space-y-6" data-testid="on-behalf-form">
                <div>
                  <Label htmlFor="campaign_id">Select Campaign *</Label>
                  <Select name="campaign_id" required>
                    <SelectTrigger data-testid="select-campaign">
                      <SelectValue placeholder="Choose a campaign" />
                    </SelectTrigger>
                    <SelectContent>
                      {campaigns.map((campaign) => (
                        <SelectItem key={campaign.id} value={campaign.id}>
                          {campaign.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="amount">Donation Amount (₹) *</Label>
                  <Input
                    id="amount"
                    name="amount"
                    type="number"
                    min="1"
                    step="1"
                    required
                    data-testid="donation-amount"
                  />
                </div>

                <div className="flex gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/volunteer/members')}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={processing}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                    data-testid="proceed-payment"
                  >
                    {processing ? 'Processing...' : 'Proceed to Payment'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default OnBehalfDonationPage;