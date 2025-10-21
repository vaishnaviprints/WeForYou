import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  ArrowLeft, 
  TrendingUp, 
  Users, 
  DollarSign, 
  Target,
  BarChart3,
  UserCheck,
  Receipt
} from 'lucide-react';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  const [campaigns, setCampaigns] = useState([]);
  const [donors, setDonors] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [campaignAnalytics, setCampaignAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!user?.roles?.includes('admin')) {
      toast.error('Access denied');
      navigate('/');
      return;
    }
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [campaignsRes, donorsRes] = await Promise.all([
        axios.get(`${API}/campaigns?status=active`),
        axios.get(`${API}/admin/donors`)
      ]);
      setCampaigns(campaignsRes.data);
      setDonors(donorsRes.data);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Session expired');
        logout();
        navigate('/');
      } else {
        toast.error('Failed to load data');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaignAnalytics = async (campaignId) => {
    try {
      const response = await axios.get(`${API}/admin/campaigns/${campaignId}/analytics`);
      setCampaignAnalytics(response.data);
      setSelectedCampaign(campaignId);
    } catch (error) {
      toast.error('Failed to load analytics');
    }
  };

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    setCreating(true);
    const formData = new FormData(e.target);

    try {
      await axios.post(`${API}/campaigns`, {
        title: formData.get('title'),
        description: formData.get('description'),
        goal_amount: parseFloat(formData.get('goal_amount')),
        currency: 'INR',
        allow_recurring: formData.get('allow_recurring') === 'on',
        image_url: formData.get('image_url') || null
      });

      toast.success('Campaign created successfully');
      e.target.reset();
      fetchInitialData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setCreating(false);
    }
  };

  const totalDonations = donors.reduce(
    (sum, donor) => sum + (donor.stats?.total_donated || 0),
    0
  );
  const totalDonors = donors.length;
  const avgDonation = totalDonors > 0 ? totalDonations / totalDonors : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/campaigns')} data-testid="back-btn">
                <ArrowLeft className="mr-2" /> Back
              </Button>
              <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
                Admin Dashboard
              </h1>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        {/* Overview Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Total Donations</p>
                  <p className="text-3xl font-bold text-blue-600">₹{totalDonations.toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Total Donors</p>
                  <p className="text-3xl font-bold text-green-600">{totalDonors}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Users className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Avg Donation</p>
                  <p className="text-3xl font-bold text-purple-600">₹{Math.round(avgDonation).toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Active Campaigns</p>
                  <p className="text-3xl font-bold text-orange-600">{campaigns.length}</p>
                </div>
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <Target className="w-6 h-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="campaigns" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 max-w-2xl">
            <TabsTrigger value="campaigns" data-testid="campaigns-tab">
              <Target className="w-4 h-4 mr-2" />
              Campaigns
            </TabsTrigger>
            <TabsTrigger value="donors" data-testid="donors-tab">
              <UserCheck className="w-4 h-4 mr-2" />
              Donors
            </TabsTrigger>
            <TabsTrigger value="create" data-testid="create-tab">
              Create Campaign
            </TabsTrigger>
          </TabsList>

          {/* Campaigns Tab */}
          <TabsContent value="campaigns">
            <div className="space-y-6">
              {campaigns.map((campaign) => (
                <Card key={campaign.id} className="border-0 shadow-lg" data-testid={`campaign-${campaign.id}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-2xl">{campaign.title}</CardTitle>
                        <CardDescription className="mt-2">
                          Goal: ₹{campaign.goal_amount.toLocaleString()} | 
                          Raised: ₹{campaign.current_amount.toLocaleString()} |
                          Donors: {campaign.donor_count}
                        </CardDescription>
                      </div>
                      <Button
                        onClick={() => fetchCampaignAnalytics(campaign.id)}
                        data-testid={`analytics-btn-${campaign.id}`}
                      >
                        <BarChart3 className="w-4 h-4 mr-2" />
                        View Analytics
                      </Button>
                    </div>
                  </CardHeader>
                  {selectedCampaign === campaign.id && campaignAnalytics && (
                    <CardContent>
                      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                        <h4 className="font-semibold text-lg">Campaign Analytics</h4>
                        <div className="grid md:grid-cols-3 gap-4">
                          <div>
                            <p className="text-sm text-gray-500">Total Raised</p>
                            <p className="text-2xl font-bold text-blue-600">
                              ₹{campaignAnalytics.stats?.total_amount?.toLocaleString() || 0}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500">Donation Count</p>
                            <p className="text-2xl font-bold text-green-600">
                              {campaignAnalytics.stats?.count || 0}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500">Avg Donation</p>
                            <p className="text-2xl font-bold text-purple-600">
                              ₹{Math.round(campaignAnalytics.stats?.avg_amount || 0).toLocaleString()}
                            </p>
                          </div>
                        </div>

                        {campaignAnalytics.top_donors?.length > 0 && (
                          <div className="mt-6">
                            <h5 className="font-semibold mb-3">Top Donors</h5>
                            <div className="space-y-2">
                              {campaignAnalytics.top_donors.map((donor, index) => (
                                <div key={index} className="flex justify-between items-center p-3 bg-white rounded-lg">
                                  <div>
                                    <p className="font-medium">{donor.name}</p>
                                    <p className="text-sm text-gray-500">{donor.email}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-semibold text-blue-600">₹{donor.total_donated.toLocaleString()}</p>
                                    <p className="text-sm text-gray-500">{donor.donation_count} donations</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Donors Tab */}
          <TabsContent value="donors">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Donor Directory</CardTitle>
                <CardDescription>All donors who have made successful donations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {donors.map((donor, index) => (
                    <div key={index} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg" data-testid={`donor-${index}`}>
                      <div>
                        <p className="font-semibold">{donor.user?.full_name}</p>
                        <p className="text-sm text-gray-500">{donor.user?.email}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-blue-600">₹{donor.stats?.total_donated?.toLocaleString() || 0}</p>
                        <p className="text-sm text-gray-500">{donor.stats?.donation_count || 0} donations</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Create Campaign Tab */}
          <TabsContent value="create">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Create New Campaign</CardTitle>
                <CardDescription>Launch a new fundraising campaign</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateCampaign} className="space-y-6" data-testid="create-campaign-form">
                  <div>
                    <Label htmlFor="title">Campaign Title *</Label>
                    <Input id="title" name="title" required data-testid="campaign-title-input" />
                  </div>

                  <div>
                    <Label htmlFor="description">Description *</Label>
                    <Textarea 
                      id="description" 
                      name="description" 
                      rows={5} 
                      required 
                      data-testid="campaign-description-input"
                    />
                  </div>

                  <div>
                    <Label htmlFor="goal_amount">Goal Amount (₹) *</Label>
                    <Input 
                      id="goal_amount" 
                      name="goal_amount" 
                      type="number" 
                      min="1" 
                      step="1" 
                      required 
                      data-testid="campaign-goal-input"
                    />
                  </div>

                  <div>
                    <Label htmlFor="image_url">Image URL (Optional)</Label>
                    <Input 
                      id="image_url" 
                      name="image_url" 
                      type="url" 
                      placeholder="https://example.com/image.jpg"
                      data-testid="campaign-image-input"
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <Label htmlFor="allow_recurring" className="font-semibold">Allow Recurring Donations</Label>
                      <p className="text-sm text-gray-500">Enable monthly pledges for this campaign</p>
                    </div>
                    <Switch id="allow_recurring" name="allow_recurring" data-testid="allow-recurring-switch" />
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full bg-blue-600 hover:bg-blue-700 h-12 text-lg" 
                    disabled={creating}
                    data-testid="create-campaign-submit"
                  >
                    {creating ? 'Creating...' : 'Create Campaign'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminDashboard;