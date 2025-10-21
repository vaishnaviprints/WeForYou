import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { ArrowLeft, Calendar, Pause, Play, XCircle, RefreshCw } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

const MyPledgesPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  const [pledges, setPledges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionPledge, setActionPledge] = useState(null);
  const [actionType, setActionType] = useState(null);

  useEffect(() => {
    fetchPledges();
  }, []);

  const fetchPledges = async () => {
    try {
      const response = await axios.get(`${API}/pledges/my`);
      setPledges(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        logout();
        navigate('/');
      } else {
        toast.error('Failed to load pledges');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePledgeAction = async (pledgeId, action) => {
    try {
      await axios.patch(`${API}/pledges/${pledgeId}?action=${action}`);
      toast.success(`Pledge ${action}d successfully`);
      fetchPledges();
      setActionPledge(null);
      setActionType(null);
    } catch (error) {
      toast.error(`Failed to ${action} pledge`);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700';
      case 'paused': return 'bg-yellow-100 text-yellow-700';
      case 'cancelled': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
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
              <Button variant="ghost" onClick={() => navigate('/my-donations')} data-testid="back-donations-btn">
                <ArrowLeft className="mr-2" /> Back
              </Button>
              <h1 className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
                My Recurring Pledges
              </h1>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12">
        {pledges.length === 0 ? (
          <Card className="border-0 shadow-lg">
            <CardContent className="py-20 text-center">
              <RefreshCw className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-600 mb-2">No Recurring Pledges</h3>
              <p className="text-gray-500 mb-6">Set up recurring donations to support causes you care about</p>
              <Button onClick={() => navigate('/campaigns')} data-testid="browse-campaigns-btn">
                Browse Campaigns
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {pledges.map((pledge) => (
              <Card key={pledge.id} className="border-0 shadow-lg" data-testid={`pledge-card-${pledge.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-2xl mb-2">Monthly Pledge</CardTitle>
                      <CardDescription>
                        Campaign ID: {pledge.campaign_id}
                      </CardDescription>
                    </div>
                    <Badge className={getStatusColor(pledge.status)}>
                      {pledge.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-gray-500">Monthly Amount</p>
                        <p className="text-2xl font-bold text-blue-600">₹{pledge.amount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Frequency</p>
                        <p className="font-medium capitalize">{pledge.frequency}</p>
                      </div>
                      {pledge.next_charge_at && pledge.status === 'active' && (
                        <div>
                          <p className="text-sm text-gray-500">Next Charge</p>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            <p className="font-medium">
                              {new Date(pledge.next_charge_at).toLocaleDateString('en-IN', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                              })}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-3 justify-center">
                      {pledge.status === 'active' && (
                        <>
                          <Button
                            variant="outline"
                            className="w-full"
                            onClick={() => {
                              setActionPledge(pledge.id);
                              setActionType('pause');
                            }}
                            data-testid={`pause-pledge-${pledge.id}`}
                          >
                            <Pause className="w-4 h-4 mr-2" />
                            Pause Pledge
                          </Button>
                          <Button
                            variant="outline"
                            className="w-full text-red-600 hover:text-red-700"
                            onClick={() => {
                              setActionPledge(pledge.id);
                              setActionType('cancel');
                            }}
                            data-testid={`cancel-pledge-${pledge.id}`}
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            Cancel Pledge
                          </Button>
                        </>
                      )}
                      {pledge.status === 'paused' && (
                        <Button
                          className="w-full bg-green-600 hover:bg-green-700"
                          onClick={() => {
                            setActionPledge(pledge.id);
                            setActionType('activate');
                          }}
                          data-testid={`activate-pledge-${pledge.id}`}
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Resume Pledge
                        </Button>
                      )}
                      {pledge.status === 'cancelled' && (
                        <p className="text-center text-gray-500 italic">This pledge has been cancelled</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!actionPledge} onOpenChange={() => setActionPledge(null)}>
        <AlertDialogContent data-testid="pledge-action-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>
              {actionType === 'cancel' ? 'Cancel Pledge?' : actionType === 'pause' ? 'Pause Pledge?' : 'Resume Pledge?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {actionType === 'cancel'
                ? 'Are you sure you want to cancel this pledge? This action cannot be undone.'
                : actionType === 'pause'
                ? 'Your pledge will be paused. You can resume it anytime.'
                : 'Your pledge will be resumed and the next charge will be scheduled.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="dialog-cancel-btn">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => handlePledgeAction(actionPledge, actionType)}
              className={actionType === 'cancel' ? 'bg-red-600 hover:bg-red-700' : ''}
              data-testid="dialog-confirm-btn"
            >
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default MyPledgesPage;