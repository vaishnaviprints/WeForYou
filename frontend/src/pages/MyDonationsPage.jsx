import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navbar from '@/components/Navbar';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Download, Receipt, Filter, TrendingUp, Calendar, CreditCard } from 'lucide-react';

const MyDonationsPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  const [donations, setDonations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchDonations();
  }, []);

  const fetchDonations = async () => {
    try {
      const response = await axios.get(`${API}/donations/my`);
      setDonations(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        logout();
        navigate('/');
      } else {
        toast.error('Failed to load donations');
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadReceipt = async (donationId) => {
    try {
      const response = await axios.get(`${API}/donations/${donationId}/receipt`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `receipt-${donationId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Receipt downloaded successfully');
    } catch (error) {
      toast.error('Failed to download receipt');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-700';
      case 'pending': return 'bg-yellow-100 text-yellow-700';
      case 'failed': return 'bg-red-100 text-red-700';
      case 'refunded': return 'bg-gray-100 text-gray-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const filteredDonations = statusFilter === 'all' 
    ? donations 
    : donations.filter(d => d.status === statusFilter);

  const totalDonated = donations
    .filter(d => d.status === 'success')
    .reduce((sum, d) => sum + d.amount, 0);

  const successfulDonations = donations.filter(d => d.status === 'success').length;

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
              <Button variant="ghost" onClick={() => navigate('/campaigns')} data-testid="back-campaigns-btn">
                <ArrowLeft className="mr-2" /> Back
              </Button>
              <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
                My Donations
              </h1>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => navigate('/my-pledges')} data-testid="my-pledges-btn">
                My Pledges
              </Button>
              {user?.roles?.includes('admin') && (
                <Button onClick={() => navigate('/admin')} data-testid="admin-btn">
                  Admin
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Total Donated</p>
                  <p className="text-3xl font-bold text-blue-600">₹{totalDonated.toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Successful Donations</p>
                  <p className="text-3xl font-bold text-green-600">{successfulDonations}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Receipt className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Total Donations</p>
                  <p className="text-3xl font-bold text-purple-600">{donations.length}</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <CreditCard className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filter */}
        <Card className="border-0 shadow-lg mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Filter className="w-5 h-5 text-gray-500" />
              <span className="text-sm font-medium">Filter by status:</span>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48" data-testid="status-filter">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="z-50">
                  <SelectItem value="all">All Donations</SelectItem>
                  <SelectItem value="success">Successful</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="refunded">Refunded</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Donations List */}
        {filteredDonations.length === 0 ? (
          <Card className="border-0 shadow-lg">
            <CardContent className="py-20 text-center">
              <Receipt className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-600 mb-2">No Donations Found</h3>
              <p className="text-gray-500 mb-6">Start making a difference today!</p>
              <Button onClick={() => navigate('/campaigns')} data-testid="browse-campaigns-btn">
                Browse Campaigns
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredDonations.map((donation) => (
              <Card key={donation.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow" data-testid={`donation-card-${donation.id}`}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-semibold">{donation.campaign_title}</h3>
                        <Badge className={getStatusColor(donation.status)}>
                          {donation.status}
                        </Badge>
                        {donation.is_anonymous && (
                          <Badge variant="outline">Anonymous</Badge>
                        )}
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-4 mt-4 text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                          <CreditCard className="w-4 h-4" />
                          <span>Amount: <span className="font-semibold text-blue-600">₹{donation.amount.toLocaleString()}</span></span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Calendar className="w-4 h-4" />
                          <span>{new Date(donation.created_at).toLocaleDateString('en-IN', { 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric' 
                          })}</span>
                        </div>
                        {donation.payment_ref && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <span className="text-xs">Payment ID: {donation.payment_ref}</span>
                          </div>
                        )}
                        {donation.want_80g && (
                          <div className="flex items-center gap-2 text-green-600">
                            <Receipt className="w-4 h-4" />
                            <span className="font-medium">80G Eligible</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="ml-4">
                      {donation.receipt && (
                        <Button
                          onClick={() => downloadReceipt(donation.id)}
                          variant="outline"
                          className="gap-2"
                          data-testid={`download-receipt-${donation.id}`}
                        >
                          <Download className="w-4 h-4" />
                          Download Receipt
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyDonationsPage;