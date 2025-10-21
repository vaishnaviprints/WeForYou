import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { ArrowLeft, Heart, Target, Calendar } from 'lucide-react';

const CampaignsPage = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API}/campaigns`);
      setCampaigns(response.data);
    } catch (error) {
      toast.error('Failed to load campaigns');
    } finally {
      setLoading(false);
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
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/')} data-testid="back-home-btn">
                <ArrowLeft className="mr-2" /> Back
              </Button>
              <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
                Active Campaigns
              </h1>
            </div>
            {user && (
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => navigate('/my-donations')} data-testid="my-donations-btn">
                  My Donations
                </Button>
                {user.roles?.includes('admin') && (
                  <Button onClick={() => navigate('/admin')} data-testid="admin-btn">
                    Admin Dashboard
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Campaigns Grid */}
      <div className="container mx-auto px-6 py-12">
        {campaigns.length === 0 ? (
          <div className="text-center py-20">
            <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-gray-600 mb-2">No Active Campaigns</h3>
            <p className="text-gray-500">Check back soon for new campaigns!</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {campaigns.map((campaign) => {
              const progress = Math.min((campaign.current_amount / campaign.goal_amount) * 100, 100);
              return (
                <Card 
                  key={campaign.id} 
                  className="hover:shadow-2xl transition-all duration-300 cursor-pointer border-0 overflow-hidden"
                  onClick={() => navigate(`/campaigns/${campaign.id}`)}
                  data-testid={`campaign-card-${campaign.id}`}
                >
                  {campaign.image_url && (
                    <div className="h-48 overflow-hidden">
                      <img 
                        src={campaign.image_url} 
                        alt={campaign.title}
                        className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                      />
                    </div>
                  )}
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <CardTitle className="text-xl">{campaign.title}</CardTitle>
                      {campaign.allow_recurring && (
                        <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                          Recurring
                        </Badge>
                      )}
                    </div>
                    <CardDescription className="line-clamp-2">
                      {campaign.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span className="font-semibold">₹{campaign.current_amount.toLocaleString()}</span>
                          <span className="text-gray-500">of ₹{campaign.goal_amount.toLocaleString()}</span>
                        </div>
                        <Progress value={progress} className="h-2" />
                        <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
                          <span>{Math.round(progress)}% funded</span>
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {campaign.donor_count} donors
                          </span>
                        </div>
                      </div>
                      <Button 
                        className="w-full bg-blue-600 hover:bg-blue-700"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/campaigns/${campaign.id}`);
                        }}
                        data-testid={`donate-btn-${campaign.id}`}
                      >
                        Donate Now
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignsPage;

import { Users } from 'lucide-react';