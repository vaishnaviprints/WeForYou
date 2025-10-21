import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AuthContext, API } from '@/App';
import { toast } from 'sonner';
import axios from 'axios';
import { Heart, Users, Target, TrendingUp, ArrowRight } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  const { user, login } = useContext(AuthContext);
  const [showAuth, setShowAuth] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);
    
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email: formData.get('email'),
        password: formData.get('password'),
        full_name: formData.get('full_name'),
        phone: formData.get('phone'),
        roles: ['donor']
      });
      
      login(response.data.access_token, response.data.user);
      toast.success('Account created successfully!');
      setShowAuth(false);
      navigate('/campaigns');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.target);
    
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.get('email'),
        password: formData.get('password')
      });
      
      login(response.data.access_token, response.data.user);
      toast.success('Logged in successfully!');
      setShowAuth(false);
      navigate('/campaigns');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-purple-50" />
        
        {/* Decorative elements */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-40 right-10 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />

        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50">
          <div className="container mx-auto px-6 py-6 flex justify-between items-center">
            <div className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
              <span className="text-blue-600">WeForYou</span> Foundation
            </div>
            <div className="flex gap-4">
              {user ? (
                <>
                  <Button onClick={() => navigate('/campaigns')} variant="ghost" data-testid="campaigns-nav-btn">
                    Campaigns
                  </Button>
                  <Button onClick={() => navigate('/my-donations')} variant="ghost" data-testid="my-donations-nav-btn">
                    My Donations
                  </Button>
                  {user.roles?.includes('admin') && (
                    <Button onClick={() => navigate('/admin')} variant="ghost" data-testid="admin-nav-btn">
                      Admin
                    </Button>
                  )}
                </>
              ) : (
                <Button onClick={() => setShowAuth(true)} className="bg-blue-600 hover:bg-blue-700" data-testid="get-started-btn">
                  Get Started
                </Button>
              )}
            </div>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 container mx-auto px-6 text-center">
          <div className="animate-fadeIn">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6" style={{ fontFamily: 'Space Grotesk' }}>
              Make a Difference
              <br />
              <span className="text-blue-600">One Donation at a Time</span>
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
              Join thousands of donors supporting meaningful causes. Track your impact, get tax benefits, and change lives.
            </p>
            <div className="flex gap-4 justify-center">
              <Button 
                onClick={() => user ? navigate('/campaigns') : setShowAuth(true)} 
                size="lg" 
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg rounded-full"
                data-testid="start-donating-btn"
              >
                Start Donating <ArrowRight className="ml-2" />
              </Button>
              <Button 
                onClick={() => navigate('/campaigns')} 
                size="lg" 
                variant="outline"
                className="px-8 py-6 text-lg rounded-full"
                data-testid="view-campaigns-btn"
              >
                View Campaigns
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 bg-white">
        <div className="container mx-auto px-6">
          <h2 className="text-4xl font-bold text-center mb-16" style={{ fontFamily: 'Space Grotesk' }}>
            Why Choose WeForYou?
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: <Heart className="w-8 h-8 text-blue-600" />,
                title: 'Verified Campaigns',
                description: 'All campaigns are verified and monitored for transparency'
              },
              {
                icon: <Users className="w-8 h-8 text-purple-600" />,
                title: 'Track Your Impact',
                description: 'See exactly where your donations go and the impact they create'
              },
              {
                icon: <Target className="w-8 h-8 text-pink-600" />,
                title: '80G Tax Benefits',
                description: 'Get tax deduction certificates instantly for eligible donations'
              },
              {
                icon: <TrendingUp className="w-8 h-8 text-green-600" />,
                title: 'Recurring Donations',
                description: 'Set up monthly donations and manage them easily'
              }
            ].map((feature, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
                <CardHeader>
                  <div className="mb-4">{feature.icon}</div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Auth Dialog */}
      <Dialog open={showAuth} onOpenChange={setShowAuth}>
        <DialogContent className="sm:max-w-md" data-testid="auth-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold">Welcome to WeForYou</DialogTitle>
          </DialogHeader>
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
              <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4" data-testid="login-form">
                <div>
                  <Label htmlFor="login-email">Email</Label>
                  <Input id="login-email" name="email" type="email" required data-testid="login-email-input" />
                </div>
                <div>
                  <Label htmlFor="login-password">Password</Label>
                  <Input id="login-password" name="password" type="password" required data-testid="login-password-input" />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit-btn">
                  {loading ? 'Loading...' : 'Login'}
                </Button>
              </form>
            </TabsContent>
            
            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4" data-testid="register-form">
                <div>
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input id="full_name" name="full_name" required data-testid="register-name-input" />
                </div>
                <div>
                  <Label htmlFor="reg-email">Email</Label>
                  <Input id="reg-email" name="email" type="email" required data-testid="register-email-input" />
                </div>
                <div>
                  <Label htmlFor="phone">Phone (Optional)</Label>
                  <Input id="phone" name="phone" type="tel" data-testid="register-phone-input" />
                </div>
                <div>
                  <Label htmlFor="reg-password">Password</Label>
                  <Input id="reg-password" name="password" type="password" required data-testid="register-password-input" />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit-btn">
                  {loading ? 'Creating Account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(20px, -50px) scale(1.1); }
          50% { transform: translate(-20px, 20px) scale(0.9); }
          75% { transform: translate(50px, 50px) scale(1.05); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default LandingPage;