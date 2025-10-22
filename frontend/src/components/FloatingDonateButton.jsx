import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Heart } from 'lucide-react';

const FloatingDonateButton = () => {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [showDialog, setShowDialog] = useState(false);
  const [amount, setAmount] = useState('');
  const [processing, setProcessing] = useState(false);

  const presetAmounts = [500, 1000, 2500, 5000];

  const handleDonate = async () => {
    if (!user) {
      toast.error('Please login to donate');
      navigate('/login');
      return;
    }

    const donationAmount = parseFloat(amount);
    if (!donationAmount || donationAmount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setProcessing(true);
    try {
      const response = await axios.post(`${API}/donations/general?amount=${donationAmount}`);
      const { donation_id, order, razorpay_key } = response.data;

      const isMock = razorpay_key === 'mock_key';

      if (isMock) {
        await axios.post(`${API}/donations/${donation_id}/verify`, {
          razorpay_order_id: order.id,
          razorpay_payment_id: `pay_mock_${Date.now()}`,
          razorpay_signature: 'mock_signature'
        });

        toast.success('Donation successful! Thank you for your support.');
        setShowDialog(false);
        setAmount('');
      } else {
        const options = {
          key: razorpay_key,
          amount: order.amount,
          currency: order.currency,
          order_id: order.id,
          name: 'WeForYou Foundation',
          description: 'General Donation',
          handler: async function (response) {
            try {
              await axios.post(`${API}/donations/${donation_id}/verify`, response);
              toast.success('Donation successful! Thank you for your support.');
              setShowDialog(false);
              setAmount('');
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

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-8 right-8 z-50">
        <Button
          onClick={() => setShowDialog(true)}
          className="h-16 w-16 rounded-full shadow-2xl bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 transition-all duration-300 hover:scale-110"
          data-testid="floating-donate-btn"
        >
          <Heart className="w-8 h-8 animate-pulse" fill="white" />
        </Button>
      </div>

      {/* Donation Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-md" data-testid="general-donation-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl flex items-center gap-2">
              <Heart className="w-6 h-6 text-red-600" />
              Support Our Foundation
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Your general donation helps us continue our mission to serve the community.
            </p>

            <div>
              <Label className="text-base font-semibold mb-3 block">Select Amount</Label>
              <div className="grid grid-cols-2 gap-3 mb-3">
                {presetAmounts.map((preset) => (
                  <Button
                    key={preset}
                    variant={amount === preset.toString() ? 'default' : 'outline'}
                    onClick={() => setAmount(preset.toString())}
                    className="h-12"
                    data-testid={`preset-${preset}`}
                  >
                    ₹{preset.toLocaleString()}
                  </Button>
                ))}
              </div>
              <Input
                type="number"
                placeholder="Enter custom amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="h-12"
                data-testid="custom-amount"
              />
            </div>

            <Button
              onClick={handleDonate}
              disabled={processing || !amount}
              className="w-full h-12 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700"
              data-testid="submit-donation"
            >
              {processing ? 'Processing...' : `Donate ₹${amount || '0'}`}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default FloatingDonateButton;